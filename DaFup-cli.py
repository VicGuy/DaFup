#!/usr/bin/python

'''
    DaFup watch face and background upload tool for Mo Young / Da Fit
    binary files.

    Author: Vic <vicpt[at]protonmail.com>
    Copyright (C) 2024 Vic

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import os
import asyncio
from bleak import BleakScanner, BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.uuids import normalize_uuid_16
import threading


''' Main characteristic uuids '''
CTRCHAR = normalize_uuid_16(0xfee2) # Write (no response)
SNDCHAR = normalize_uuid_16(0xfee6) # Send data
NTYCHAR = normalize_uuid_16(0xfee3) # Notify
MANCHAR = normalize_uuid_16(0x2a29) # Manufacturer name


''' Main Window '''
class DaFup:
    
    def __init__(self):
        self.DevSelected = ""
        self.FileSelected = ""
        self.NotifyData = ""
        self.liststore = []
        self.IsFace = False
        self.IsBackground = False

    '''Main method'''
    def main(self):
        self.search_request()
        
        #Select device menu
        mstatus = False
        while not mstatus:
            n = input("Select device to connect or [s] for new search [q] to Quit): ")
            if (n == 's'):
                self.search_request()
            elif (n == 'q'):
                quit()
            elif (n.isdigit()):
                mstatus = True
            else:
                print ("Need to be a number, s or q")
        
        print (self.liststore[int(n)][0] + " selected.")
        self.DevSelected = self.liststore[int(n)][0]
        
        #Select file type menu
        self.IsBackground = False
        self.IsFace = False
        mstatus = False
        while not mstatus:
            n = input("Select what to upload [b] for background [f] to watch face [q] to Quit): ")
            if (n == 'b'):
                self.IsBackground = True
                mstatus = True
            elif (n == 'f'):
                self.IsFace = True
                mstatus = True
            elif (n == 'q'):
                quit()
            else:
                print ("Need to be b, f or q")
        
        if (n == "b"):
            n = "Background"
        else:
            n = "Watch face"
        print (n + " selected.")
        
        #Select file menu
        mstatus = False
        while not mstatus:
            n = input("Type the path of file to upload or just [q] to Quit): ")
            if (n == 'q'):
                quit()
            else:
                if (os.path.exists(n)):
                    self.FileSelected = n
                    mstatus = True
                else:
                    print ("[ERROR] Error opening the file.")
        
        print (n + " selected.")
        
        self.upload_request()
    
    ''' Discover bluetooth devices '''
    async def Discover(self):
        #Scanning for 5 seconds...
        devices = await BleakScanner.discover(
        return_adv=True)
        
        return devices

    ''' Connect to device '''
    async def DoConnect(self):
        # Main connection
        client = BleakClient(self.DevSelected)
        try:
            await client.connect()
        except:
            print ("[ERROR] Can't connect to device.")
            return
        
        # Check if device has a moyoung manufacture characteristic
        try:
            manfact = await client.read_gatt_char(MANCHAR)
        except:
            print ("[ERROR] It doesn't look a MOYOUNG-V2 compatible device.")
            return
        
        # Check if device manufacture characteristic reads as a moyoung
        if (manfact.decode("utf-8") != "MOYOUNG-V2"):
            await client.disconnect()
            print ("[ERROR] It doesn't look a MOYOUNG-V2 compatible device.")
            return
        else:
            
            # Start notify system, self.callback() handle it
            await client.start_notify(NTYCHAR, self.callback)
            
            # Open the file to send
            fsize, flist = self.OpenFile(self.FileSelected)
            
            # Background or watch face
            if (self.IsBackground):
                cmd = self.cmdSendBackground(fsize)
            else:
                cmd = self.cmdSendFace(fsize)
            # Send start transfer command
            await client.write_gatt_char(CTRCHAR, cmd, response=False)
            await asyncio.sleep(0.5)
            
            print ("Transferring...")
            progress = 0
            # Start transfer, while not get "feea200974ff"
            while (self.NotifyData[0:6] != b"\xfe\xea\x20\x09\x74\xff"):
                for i in range(0, len(flist)):
                    await client.write_gatt_char(SNDCHAR, flist[i], response=False)
                    #print (str(self.NotifyData[0:6])) #Debug
                    #self.progress.set_fraction(self.progress.get_fraction() + (1/len(flist)))
                    progress += 100/len(flist)
                    print (str(int(progress)) + "%")
                    await asyncio.sleep(0.2)
                break
                #It will break after transfer complete. Need to find out how the
                #checksum is made to then do a proper checksum comparison.
            
            # Send finish command
            # Background or watch face
            if (self.IsBackground):
                cmd = self.cmdBackTransferFinish()
                await client.write_gatt_char(CTRCHAR, cmd, response=False)
                cmd = self.cmdSetBackTransfer()
                await client.write_gatt_char(CTRCHAR, cmd, response=False)
                cmd = self.cmdSetFace(1)
                await client.write_gatt_char(CTRCHAR, cmd, response=False)
            else:
                cmd = self.cmdFaceTransferFinish()
                await client.write_gatt_char(CTRCHAR, cmd, response=False)
                cmd = self.cmdSetFaceTransfer()
                await client.write_gatt_char(CTRCHAR, cmd, response=False)
                cmd = self.cmdSetFace(6)
                await client.write_gatt_char(CTRCHAR, cmd, response=False)
            
            await client.disconnect()
            print ("\nTransfer complete.")
            
    ''' Function that handles service characteristic notification '''
    def callback(self, sender: BleakGATTCharacteristic, data: bytearray):
        self.NotifyData = data        
    
    ''' Open a file for send '''
    def OpenFile(self, filen=""):
        if (filen == ""): return
        try:
            # Open and divide the file in chunks
            fo = open(filen, "rb")
        except:
            print ("[ERROR] Error opening the file.")

        chunk = 512
        flist = []
        while (True):
            data = fo.read(chunk)
            if (data == b''): break
            flist.append(data)

        fo.seek(0,0)
        fsize = len(fo.read())
        fo.close()
    
        return fsize, flist
    
    ''' Face transfer cmd '''
    def cmdSendFace(self, length=0):
        header  = bytes.fromhex("feea200974")
        length  = length.to_bytes(4)
    
        cmd = (header + length)
        return cmd
    
    ''' Face transfer finish signal cmd '''
    def cmdFaceTransferFinish(self):
        header  = bytes.fromhex("feea20097400000000")
    
        cmd = header
        return cmd
    
    ''' Set face transfer cmd (unknown yet) '''
    def cmdSetFaceTransfer(self):
        header  = bytes.fromhex("feea200ab41130040000")
    
        cmd = header
        return cmd
    
    ''' Background transfer cmd '''
    def cmdSendBackground(self, length=0):
        header  = bytes.fromhex("feea20096e")
        length  = length.to_bytes(4)
    
        cmd = (header + length)
        return cmd
    
    ''' Background transfer finish signal cmd '''
    def cmdBackTransferFinish(self):
        header  = bytes.fromhex("feea20096e00000000")
    
        cmd = header
        return cmd
    
    ''' Set background transfer cmd (unknown yet) '''
    def cmdSetBackTransfer(self):
        header  = bytes.fromhex("feea200529")
    
        cmd = header
        return cmd
    
    ''' Set watch face '''
    def cmdSetFace(self, face=0):
        if (face > 6): return 0
    
        header  = bytes.fromhex("feea200619")
        face    = face.to_bytes(1)
    
        cmd = (header + face)
        return cmd
        
    '''On search request'''
    def search_request(self):
        print ("Searching for devices, please wait...")
        
        self.liststore.clear()
        d = 0
        devices = asyncio.run(self.Discover())
        for x in devices:
            devlist = str(devices[x][0]).split(': ')
            self.liststore.append([devlist[0], devlist[1]])
            d += 1
        
        #List the devices
        for i in range(0, len(self.liststore)):
            print ('----------------------------------------')
            print ("[" + str(i) + "] " + self.liststore[i][0] +
            " - " +self.liststore[i][1])
        
        print ("\nScan complete, " + str(d) + " devices found")
    
    '''On upload request'''
    def upload_request(self):
        print ("Trying to connect to device, please wait...")
        asyncio.run(self.DoConnect())
        

if __name__ == "__main__":
    dafup = DaFup()
    dafup.main()
