#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys, os, zipfile, sys, time

# Import PyQt5 libraries for generating the GUI application.
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtCore import QThread, pyqtSignal

# Import GUI window.
import mainWindow
import kiban

FILE_COUNT = 0

def alert(title, message, icon, info, detailed):
    # Create a message box object.
    msg = QMessageBox()
    
    # Set parameters for the message box.
    msg.setIcon(icon)
    msg.setWindowTitle(title)
    msg.setText(message)
    
    # Generate additional information if exists.
    if not info == None:
        msg.setInformativeText(info)
    if not detailed == None:
        msg.setDetailedText(detailed)
    
    # Show the message box.    
    msg.exec_()

def unZip(in_path, out_path):
    zip_ref = zipfile.ZipFile(in_path, 'r')
    zip_ref.extractall(out_path)
    zip_ref.close()

def getFile(dir_name, srch_ext):
    lst_xml = []
    lst_files = os.listdir(dir_name)
    
    for lst_file in lst_files:
        file_name, file_ext = os.path.splitext(lst_file)
        if file_ext == srch_ext:
            lst_xml.append(os.path.join(dir_name, lst_file))
    return(lst_xml)

def getDir(dir_name, srch_ext):
    lst_xml = []
    srch_dirs = os.listdir(dir_name)
    
    for srch_dir in srch_dirs:
        if os.path.isdir(os.path.join(dir_name, srch_dir)):
            lst_xml = lst_xml + getFile(os.path.join(dir_name, srch_dir), srch_ext)
        else:
            lst_files = os.listdir(dir_name)
            
            for lst_file in lst_files:
                file_name, file_ext = os.path.splitext(lst_file)
                if file_ext == srch_ext:
                    lst_xml.append(os.path.join(dir_name, lst_file))
    return(lst_xml)

class KibanConverter(QThread):
    countChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super(KibanConverter, self).__init__(parent)
        
        # Initialyze attributes for this class.
        self.xml_files = None   # The list of input files.
        self.out_dir = None     # The output directory.
        self.feat_type = None   # Selected feature type.
        self.file_num = None    # Number of files for parsing.
    
    def setup(self, xml_files, out_dir, feat_type):
        self.xml_files = xml_files
        self.out_dir = out_dir
        self.feat_type = feat_type
        self.file_num = len(self.xml_files)
    
    def run(self):
        # Initialyze the counter.
        count = 0
        
        for xml_file in self.xml_files:
            # Select the input feature type.
            if self.feat_type == 0:
                # The case for base items.
                kiban.convertBase(xml_file, self.out_dir)
            elif self.feat_type == 1:
                # The case for DEM items.
                kiban.convertDem(xml_file, self.out_dir)
            else:
                # Create error messages if the given feature type is invalid.
                error_title = "Error occured!!"
                error_msg = "Selected feature type is invalid."
                error_info = "Please check valid feature type agin."
                error_icon = QMessageBox.Critical
                error_detailed = ""
                
                # Handle error.
                alert(title=error_title, message=error_msg, icon=error_icon, info=error_info, detailed=error_detailed)
                
                # Stop the process.
                return(None)
            
            # Calculate prgress in percentage.
            prog = (float(count) / float(self.file_num - 1)) * 100
            
            # Emit the value.
            self.countChanged.emit(int(prog))
            
            # Update the counter.
            count = count + 1

class mainPanel(QMainWindow, mainWindow.Ui_MainWindow):
    def __init__(self, parent=None):
        # Make this class as the super class and initialyze the class.
        super(mainPanel, self).__init__(parent)
        self.setupUi(self)
        
        # Initialize progress bars.
        self.pbr_proc_files.setMaximum(100)                                    
        self.pbr_proc_files.setValue(0)
        
        # Activate operation mode selecting button.
        self.btn_in_dir.clicked.connect(self.getTheInputDirectory)
        self.btn_out_dir.clicked.connect(self.getTheOutputDirectory)
        
        # Initialyzing the button group for the feature types.
        self.grp_feat_type = QButtonGroup()
        self.grp_feat_type.addButton(self.rad_feat_type_base, 0)
        self.grp_feat_type.addButton(self.rad_feat_type_mesh, 1)
        
        # Initialyze the radio button for selecting feature types.
        self.rad_feat_type_base.setChecked(True)
        
        # Initialyze the convert button.
        self.btn_convert.clicked.connect(self.convert)
        
        self.converter = KibanConverter()
        self.converter.countChanged.connect(self.onCountChanged)
    
    def getTheInputDirectory(self):
        # Define directories for storing files.
        in_dir = QFileDialog.getExistingDirectory(self, "Select the input directory.")
        
        if not os.path.exists(in_dir):
            # Create error messages.
            error_title = "Error occured!!"
            error_msg = "Invalid input directory is selected."
            error_info = "Please select existing directory."
            error_icon = QMessageBox.Critical
            error_detailed = "The XML files sotred in the directory should be unziped!!"
            
            # Handle error.
            alert(title=error_title, message=error_msg, icon=error_icon, info=error_info, detailed=error_detailed)
            
            # Returns nothing.
            return(None)
        else:
            # Input the directory name to the input box.
            self.tbx_in_dir.setText(in_dir)
            
            # Returns the input directory for parsing.
            return(in_dir)
    
    def getTheOutputDirectory(self): 
        # Define directories for storing files.
        out_dir = QFileDialog.getExistingDirectory(self, "Select the output directory.")
        
        if not os.path.exists(out_dir):
            # Create error messages.
            error_title = "Error occured!!"
            error_msg = "Invalid output directory is selected."
            error_info = "Please select valid directory."
            error_icon = QMessageBox.Critical
            error_detailed = "Please check permission settings for the output directory."
            
            # Handle error.
            alert(title=error_title, message=error_msg, icon=error_icon, info=error_info, detailed=error_detailed)
            
            # Returns nothing.
            return(None)
        else:
            # Input the directory name to the input box.
            self.tbx_out_dir.setText(out_dir)
            
            # Returns the output directory for putting outcomes.
            return(out_dir)
    
    def convert(self):
        # Initialyze the progress bar.
        self.pbr_proc_files.setValue(0)
        
        # Get the input directory from text box.
        in_dir = self.tbx_in_dir.text()
        
        # Check the given input directory exists.
        if not os.path.exists(in_dir):
            # Create error messages.
            error_title = "Error occured!!"
            error_msg = "Invalid input directory is selected."
            error_info = "Invalid input directory is selected."
            error_icon = QMessageBox.Critical
            error_detailed = ""
            
            # Handle error.
            alert(title=error_title, message=error_msg, icon=error_icon, info=error_info, detailed=error_detailed)
            
            # Returns nothing.
            return(None)
        
        # Get the output directory from text box.
        out_dir = self.tbx_out_dir.text()
        
        # Check the given output directory exists.
        if not os.path.exists(out_dir):
            # Create error messages.
            error_title = "Error occured!!"
            error_msg = "Invalid output directory is selected."
            error_info = "Invalid output directory is selected."
            error_icon = QMessageBox.Critical
            error_detailed = ""
            
            # Handle error.
            alert(title=error_title, message=error_msg, icon=error_icon, info=error_info, detailed=error_detailed)
            
            # Returns nothing.
            return(None)
        
        # Get XML files stored in the input directories.
        xml_files = getDir(in_dir, ".xml")
        
        # Get the feature type for converting: 0 for basic items, and 1 for DEM items.
        feat_type = self.grp_feat_type.checkedId()
        
        # Initialyze the Kiban Chizu converter.
        self.converter.setup(xml_files, out_dir, feat_type)
        
        # Start threading.
        self.converter.start()
        
        # Finally set the progress bar value with 0.
        self.pbr_proc_files.setValue(0)
        
    def onCountChanged(self, value):
        # Update the progress bar.
        self.pbr_proc_files.setValue(value)

def main():
    app = QApplication(sys.argv)
    form = mainPanel()
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()
