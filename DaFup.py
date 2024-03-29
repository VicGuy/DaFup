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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

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
class MainWindow:
    
    def __init__(self):
        self.SetMainWindow()
        self.SetWidgets()
        self.ConnectSignals()
        self.DevSelected = ""
        self.FileSelected = ""
        self.NotifyData = ""
        
    '''Set main window'''
    def SetMainWindow(self):
        self.window = Gtk.Window()
        self.window.set_decorated(False)
        self.window.set_size_request(800, 600)
        self.window.set_resizable(True)
        self.window.set_position(1)
        self.window.set_title("DaFup")
    
    '''Set widgets'''
    def SetWidgets(self):
        ### Menu ###
        self.filemenu = Gtk.Menu()
        self.msearch = Gtk.MenuItem.new_with_label("Search")
        self.filemenu.append(self.msearch)
        self.mexit = Gtk.MenuItem.new_with_label("Exit")
        self.filemenu.append(self.mexit)
        self.filemenu.show_all()
        
        ### Menu button ###
        self.mbutton = Gtk.MenuButton()
        self.mbutton.set_popup(self.filemenu)
        self.mbutton.show()
        
        ### Header ###
        self.header = Gtk.HeaderBar()
        self.header.pack_start(self.mbutton)
        self.header.set_title("DaFup")
        self.header.show()
        
        ### Liststore ###
        self.liststore = Gtk.ListStore(str, str)
        
        ### Treeview ###
        self.treeview = Gtk.TreeView(model=self.liststore)
        self.treeview_select = self.treeview.get_selection()
        self.treeview.show()
        
        ### Column Mac address ###
        self.render_two = Gtk.CellRendererText()
        self.column_mac = Gtk.TreeViewColumn("MAC Address", self.render_two, text=0)
        self.treeview.append_column(self.column_mac)
        
        ### Column Name ###
        self.render_one = Gtk.CellRendererText()
        self.column_name = Gtk.TreeViewColumn("Name", self.render_one, text=1)
        self.treeview.append_column(self.column_name)
        
        ### Separator ###
        self.huseparator = Gtk.HSeparator()
        self.huseparator.show()
        
        ### Separator ###
        self.vlseparator = Gtk.VSeparator()
        self.vlseparator.show()
        
        ### Upload label ###
        self.uplabel = Gtk.Label.new("Upload:")
        self.uplabel.show()
        
        ### Background / Face radio button
        self.rback = Gtk.RadioButton.new_with_label_from_widget(None, "Background")
        self.rback.show()
        self.rface = Gtk.RadioButton.new_from_widget(self.rback)
        self.rface.set_label("Face")
        self.rface.show()
        
        ### File chooser button ###
        self.fbutton = Gtk.FileChooserButton(title="Select file")
        self.fbutton.show()
        
        ### Separator ###
        self.vrseparator = Gtk.VSeparator()
        self.vrseparator.show()
        
        ### Upload button ###
        self.upbutton = Gtk.Button.new_with_label("Upload")
        self.upbutton.set_sensitive(False)
        self.upbutton.show()
        
        ### Progress bar ###
        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(True)
        self.progress.show()
        
        ### Separator ###
        self.hlseparator = Gtk.HSeparator()
        self.hlseparator.show()
        
        ### Status bar ###
        self.statusb = Gtk.Statusbar()
        self.statusb.push(0, "Initialized")
        self.statusb.show()
        
        ### First BoxContainer ###
        self.FirstContainer = Gtk.HBox()
        self.FirstContainer.pack_start(self.vlseparator, False, False, 4)
        self.FirstContainer.pack_start(self.uplabel, False, False, 4)
        self.FirstContainer.pack_start(self.rback, False, False, 4)
        self.FirstContainer.pack_start(self.rface, False, False, 4)
        self.FirstContainer.pack_start(self.fbutton, False, False, 4)
        self.FirstContainer.pack_start(self.vrseparator, False, False, 4)
        self.FirstContainer.pack_start(self.upbutton, False, False, 4)
        self.FirstContainer.pack_start(self.progress, True, True, 10)
        self.FirstContainer.show()
                
        #### Main BoxContainer ###
        self.MainContainer = Gtk.VBox()
        self.MainContainer.pack_start(self.header, False, True, 0)
        self.MainContainer.pack_start(self.treeview, True, True, 2)
        self.MainContainer.pack_start(self.huseparator, False, False, 8)
        self.MainContainer.pack_start(self.FirstContainer, False, True, 0)
        self.MainContainer.pack_start(self.hlseparator, False, False, 8)
        self.MainContainer.pack_start(self.statusb, False, False, 0)
        self.MainContainer.show()
        
        ### Main Window ###
        self.window.add(self.MainContainer)
        self.window.show()
    
    
    '''Connect all signals'''
    def ConnectSignals(self):
        #Quit signal
        self.window.connect("destroy", self.QuitMain)
        
        #Menu signals
        self.mexit.connect("activate", Gtk.main_quit)
        self.msearch.connect("activate", self.on_search_button)        
        
        #Button signals
        self.upbutton.connect("clicked", self.on_upbutton_button)
        self.fbutton.connect("file-set", self.FileChanged)
        
        #Tree view signals
        self.treeview_select.connect("changed", self.on_tree_selection)


    '''Main method'''
    def main(self):
        Gtk.main()

    '''On quit'''
    def QuitMain(self, arg1):
        Gtk.main_quit()
    
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
        except Exception:
            self.UpdateStatus("[ERROR] Can't connect to device.")
            self.upbutton.set_sensitive(True)
            return
        
        # Check if device has a moyoung manufacture characteristic
        try:
            manfact = await client.read_gatt_char(MANCHAR)
        except Exception:
            self.UpdateStatus("[ERROR] It doesn't look a MOYOUNG-V2 compatible device.")
            return
        
         # Check if device manufacture characteristic reads as a moyoung
        if (manfact.decode("utf-8") != "MOYOUNG-V2"):
            await client.disconnect()
            self.UpdateStatus("[ERROR] It doesn't look a MOYOUNG-V2 compatible device.")
            return
        else:
            
            # Start notify system, self.callback() handle it
            await client.start_notify(NTYCHAR, self.callback)
            
            # Open the file to send
            try:
                fsize, flist = self.OpenFile(self.FileSelected)
            except Exception:
                return
            
            # Background or watch face
            if (self.rback.get_active()):
                cmd = self.cmdSendBackground(fsize)
            else:
                cmd = self.cmdSendFace(fsize)
            # Send start transfer command
            await client.write_gatt_char(CTRCHAR, cmd, response=False)
            await asyncio.sleep(0.5)
            
            self.UpdateStatus("Transferring...")
            self.progress.set_fraction(0)
            # Start transfer, while not get "feea200974ff"
            while (self.NotifyData[0:6] != b"\xfe\xea\x20\x09\x74\xff"):
                for i in range(0, len(flist)):
                    await client.write_gatt_char(SNDCHAR, flist[i], response=False)
                    #print (str(self.NotifyData[0:6])) #Debug
                    self.progress.set_fraction(self.progress.get_fraction() + (1/len(flist)))
                    await asyncio.sleep(0.2)
                break
                #It will break after transfer complete. Need to find out how the
                #checksum is made to then do a proper checksum comparison.
            
            # Send finish command
            # Background or watch face
            if (self.rback.get_active()):
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
            self.upbutton.set_sensitive(True)
            self.UpdateStatus("Transfer complete.")
            
    ''' Function that handles service characteristic notification '''
    def callback(self, sender: BleakGATTCharacteristic, data: bytearray):
        self.NotifyData = data        
    
    ''' Update status bar '''
    def UpdateStatus(self, text="test"):
        self.statusb.push(0, text)
    
    ''' Open a file for send '''
    def OpenFile(self, filen=""):
        if (filen == ""): return
        # Open and divide the file in chunks
        try:
            fo = open(filen, "rb")
        except Exception:
            self.UpdateStatus("[ERROR] Opening file.")
            return
            
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
        
    '''On search button press'''
    def on_search_button(self, arg1):
        self.UpdateStatus("Searching for devices, please wait...")
        thread = threading.Thread(target=self.search_button)
        thread.daemon = True
        thread.start()
        
    '''On search button func call'''
    def search_button(self):
        self.liststore.clear()
        i = 0
        devices = asyncio.run(self.Discover())
        for x in devices:
            devlist = str(devices[x][0]).split(': ')
            self.liststore.append([devlist[0], devlist[1]])
            i += 1
        
        self.UpdateStatus("Scan complete, " + str(i) + " devices found")
    
    '''On button upload'''
    def on_upbutton_button(self, button):
        thread = threading.Thread(target=self.upbutton_button)
        thread.daemon = True
        thread.start()
    
    '''On button upload func call'''
    def upbutton_button(self):
        self.upbutton.set_sensitive(False)
        self.UpdateStatus("Trying to connect to device, please wait...")
        if (self.FileSelected == ""):
            self.UpdateStatus("[ERROR] No file selected.")
            return
        asyncio.run(self.DoConnect())
        
    '''Chosen file'''
    def FileChanged(self, chosenfile):
        self.FileSelected = chosenfile.get_filename()
    
    '''On tree view selection'''
    def on_tree_selection(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            self.DevSelected = model[treeiter][0]
        
        self.upbutton.set_sensitive(True)


if __name__ == "__main__":
    mWindow = MainWindow()
    mWindow.main()
