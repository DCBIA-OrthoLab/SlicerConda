import logging
import os
from typing import Annotated, Optional

import vtk

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

import sys
import io
import time
import platform

import subprocess
import shutil
import urllib
import multiprocessing
from qt import (QFileDialog,QSettings,QDialogButtonBox,QComboBox,QVBoxLayout,QDialog,QLabel,QWidget,QApplication,QListWidget,QPushButton,QLineEdit,QMessageBox,QHBoxLayout,QTimer)
import threading
import tempfile
#
# CondaSetUp
#


class CondaSetUp(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("CondaSetUp")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = ["Slicer Conda"]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Leroux Gaelle (UoM)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#CondaSetUp">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""")

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """Add data sets to Sample Data module."""
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # CondaSetUp1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="CondaSetUp",
        sampleName="CondaSetUp1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "CondaSetUp1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="CondaSetUp1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="CondaSetUp1",
    )

    # CondaSetUp2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="CondaSetUp",
        sampleName="CondaSetUp2",
        thumbnailFileName=os.path.join(iconsPath, "CondaSetUp2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="CondaSetUp2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="CondaSetUp2",
    )


#
# CondaSetUpParameterNode
#


@parameterNodeWrapper
class CondaSetUpParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """

    a = 1


#
# CondaSetUpWidget
#
class UserSelectorDialog(QDialog, VTKObservationMixin):
    '''
    This class create a custom dialog window for selecting a user from a dropdown list.
    Here it's using to create a dialog box to choose the user in WSL.
    '''
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for VTK observation

        self.setWindowTitle('Select User')
        layout = QVBoxLayout(self)

        # Add a label at the top of the dialog
        label = QLabel("Please select your username:")
        layout.addWidget(label)

        self.comboBox = QComboBox()
        layout.addWidget(self.comboBox)

        # Create OK and Cancel buttons
        buttonBox = QDialogButtonBox()
        buttonBox.addButton(buttonBox.Ok)
        buttonBox.addButton(buttonBox.Cancel)
        buttonBox.accepted.connect(self.accept)  # Connect the accepted signal to the accept slot
        buttonBox.rejected.connect(self.reject)  # Connect the rejected signal to the reject slot
        layout.addWidget(buttonBox)  # Add the button box to the layout

        self.setLayout(layout)  # Set the layout on the dialog

    def addUser(self, username):
        '''
        Add items to the dialog windows
        '''
        self.comboBox.addItem(username)

    def selectedUser(self):
        return self.comboBox.currentText

class DeselectableListWidget(QListWidget):
    '''
    This class extends the QListWidget to create a list widget with a custom feature: the ability to deselect all items by clicking on an empty area within the widget.
    When the user clicks on a part of the list widget that does not contain an item, any currently selected items are deselected.
    '''

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if not item:
            self.clearSelection()
            self.setCurrentItem(None)
        QListWidget.mousePressEvent(self, event)


class FileManagerWidget(QDialog):
    '''
    class that extends QDialog to create a custom file manager for navigating and managing directories within a WSL environment.
    It includes functionality for navigating directories, creating and deleting directories, and selecting a directory for installation purposes.
    '''
    def __init__(self):
        super().__init__()

        self.user = self.initUser()
        self.currentPath = "/home/"+self.user
        self.choosePath = "/home/"+self.user

        self.directories = self.getWSLDirectories()
        self.initUI()

    def initUser(self):
        '''
        Determines the current user by running a shell command in WSL and opens a dialog for the user to select their username.
        '''       
        script_content = f"""
python3 -c 'import CondaSetUp_wsl_utils.test as check; import os; print(os.path.isfile(check.__file__))'
awk -F ':' '{{{{ if ($3 >= 1000 && $1 != "nobody") printf "%s\\n", $1 }}}}' /etc/passwd
"""

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".sh", mode='w', newline='\n') as temp_script:
                temp_script.write(script_content.strip())
                temp_script_path = temp_script.name

            temp_script_path_wsl = self.windows_to_linux_path(temp_script_path)
            print("temp_script_path_wsl :", temp_script_path_wsl)
            result = subprocess.run(["wsl", "bash", temp_script_path_wsl], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Script executed successfully")
                print("stdout:", result.stdout)
                # decoded_stdout = result.stdout.decode('utf-8')
                users = result.stdout.strip().split('\n')
                print("users : ",users)
            else:
                print("Command failed with return code:", result.returncode)
                print("stdout:", result.stdout)
                print("stderr:", result.stderr)
        except subprocess.CalledProcessError as e:
            print("Failed to execute script:", e)
            print("Output:", e.output)
            print("Error:", e.stderr)
        finally:
            # Nettoyer le fichier temporaire
            try:
                os.remove(temp_script_path)
            except OSError:
                pass

        dialog = UserSelectorDialog(slicer.util.mainWindow())
        for user in users:
            dialog.addUser(user)

        if dialog.exec_():
            selected_user = dialog.selectedUser()
            print("Selected user:", selected_user)
            return selected_user
        return None
    

    def windows_to_linux_path(self,windows_path):
            '''
        Convert a windows path to a path that wsl can read
        '''
            windows_path = windows_path.strip()

            path = windows_path.replace('\\', '/')

            if ':' in path:
                drive, path_without_drive = path.split(':', 1)
                path = "/mnt/" + drive.lower() + path_without_drive

            return path

    def initUI(self):
        '''
        Sets up the user interface of the file manager, including layout, buttons, and directory list widget.
        '''


        self.setWindowTitle("Gestionnaire de Fichiers WSL")

        mainLayout = QVBoxLayout()

        pathLayout = QHBoxLayout()
        self.pathLabel = QLabel(self.currentPath)
        pathLayout.addWidget(self.pathLabel)
        pathLayout.addStretch(1)

        self.backButton = QPushButton("Back")
        self.backButton.clicked.connect(self.navigateUp)
        pathLayout.addWidget(self.backButton)

        mainLayout.addLayout(pathLayout)

        self.dirListWidget = DeselectableListWidget()
        self.dirListWidget.itemDoubleClicked.connect(self.navigateIntoDirectory)
        mainLayout.addWidget(self.dirListWidget)

        actionButtonLayout = QHBoxLayout()

        self.deleteButton = QPushButton("Delete folder")
        self.deleteButton.clicked.connect(self.deleteDirectory)
        actionButtonLayout.addWidget(self.deleteButton)

        self.createDirButton = QPushButton("Create folder")
        self.createDirButton.clicked.connect(self.createDirectory)
        actionButtonLayout.addWidget(self.createDirButton)

        createFolderLayout = QHBoxLayout()
        newFolderLabel = QLabel("Name of the new folder:")
        self.newDirNameEdit = QLineEdit()
        createFolderLayout.addWidget(newFolderLabel)
        createFolderLayout.addWidget(self.newDirNameEdit)

        mainLayout.addLayout(createFolderLayout)

        self.installButton = QPushButton("Choose this folder")
        self.installButton.clicked.connect(self.installHere)
        actionButtonLayout.addWidget(self.installButton)

        mainLayout.addLayout(actionButtonLayout)

        self.setLayout(mainLayout)

        self.refreshDirectories()
        self.refreshBackButtonState()


    def refreshPathLabel(self):
        '''
        Updates the label showing the current path in the file manager.
        '''
        self.pathLabel.setText(self.currentPath)

    def refreshBackButtonState(self):
        '''
        Enables or disables the back button based on the current directory path.
        '''
        self.backButton.setEnabled(self.currentPath != "/home/"+self.user)

    def deleteDirectory(self):
        '''
        Deletes the selected directory after confirmation from the user.
        '''
        selectedDir = self.dirListWidget.currentItem()
        if selectedDir:
            selectedDirPath = self.currentPath+"/"+selectedDir.text()
            reply = QMessageBox.question(self, 'Confirmation',
                                         f"Are you sure you want to delete this folder : '{selectedDirPath}'?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                try:
                    command = ["wsl", "--user", self.user, "--", "rm", "-rf", selectedDirPath]
                    subprocess.check_output(command)
                    self.refreshDirectories()
                except subprocess.CalledProcessError as e:
                    QMessageBox.warning(self, "Error", f"Can't delete the folder : {e}")
        else:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un dossier à supprimer.")

    def getWSLDirectories(self):
        '''
        Retrieves a list of directories in the current WSL path.
        '''
        command = ["wsl", "--user", self.user, "--", "bash", "-c", f"ls -d {self.currentPath}/*/"]
        try:
            result = subprocess.check_output(command, stderr=subprocess.STDOUT)
            directories = [os.path.basename(dir.strip('/')) for dir in result.decode().strip().split('\n') if dir]
            return directories
        except subprocess.CalledProcessError as e:
            error = e.output.decode()
            if "No such file or directory" in error:
                return []
            else:
                print(f"An error has occured : {e}")
                return []


    def navigateIntoDirectory(self, item):
        '''
        Navigates into the directory selected by the user.
        '''
        self.currentPath = self.currentPath+"/"+ item.text()
        self.refreshPathLabel()
        self.refreshDirectories()
        self.refreshBackButtonState()

    def navigateUp(self):
        '''
        Navigates one level up in the directory hierarchy.
        '''
        self.currentPath = os.path.dirname(self.currentPath)
        self.refreshPathLabel()
        self.refreshDirectories()
        self.refreshBackButtonState()

    def createDirectory(self):
        '''
        Creates a new directory with the specified name in the current path.
        '''
        newDirName = self.newDirNameEdit.text
        if newDirName:
            try:
                subprocess.check_output(["wsl", "--user", self.user, "--", "mkdir", self.currentPath+"/"+newDirName])
                self.refreshDirectories()
            except subprocess.CalledProcessError as e:
                QMessageBox.warning(self, "Error", f"Impossible to create the folder : {e}")
        else:
            QMessageBox.warning(self, "Error", "Enter a folder name")

    def refreshDirectories(self):
        '''
        Refreshes the list of directories displayed in the file manager.
        '''
        self.dirListWidget.clear()
        self.dirListWidget.addItems(self.getWSLDirectories())
        self.refreshBackButtonState()


    def installHere(self):
        '''
        Sets the chosen path for installation based on the selected directory and closes the dialog.
        '''
        currentItem = self.dirListWidget.currentItem()
        if currentItem is not None:
            selectedDir = currentItem.text()
            self.choosePath = f"{self.currentPath}/{selectedDir}"
        else:
            self.choosePath = f"{self.currentPath}"
        print("choosePath : ",self.choosePath)
        self.close()

    def getUserName(self):
        '''
        Returns the username of the current user.
        '''
        return self.user

    def getChoosePath(self):
        '''
        Returns the chosen path for installation.
        '''
        return self.choosePath


class CondaSetUpWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/CondaSetUp.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = CondaSetUpLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        self.conda = CondaSetUpCall()

        if platform.system() == "Windows" :
            self.conda_wsl = CondaSetUpCallWsl()

        self.ui.outputsCollapsibleButton.setText("Installation miniconda3")
        self.ui.outputsCollapsibleButton.collapsed = True

        # Buttons
        self.ui.buttonCondaFolder.connect("clicked(bool)", self.chooseCondaFolder)
        self.ui.TestEnvButton.connect("clicked(bool)", self.testEnv)
        self.ui.folderInstallButton.connect("clicked(bool)", self.chooseInstallFolder)
        self.ui.installButton.connect("clicked(bool)", self.installMiniconda)
        self.ui.CreateEnvButton.connect("clicked(bool)", self.createEnv)
        self.ui.deletePushButton.connect("clicked(bool)",self.deleteEnv)
        self.ui.checkBoxWsl.connect("clicked(bool)",self.checkboxChangeWsl)

        self.ui.checkBoxWsl.setHidden(True)

        if platform.system() == "Windows":
            self.ui.checkBoxWsl.setHidden(False)

        #Hidden
        self.ui.timeInstallation.setHidden(True)
        self.ui.timeCreationEnv.setHidden(True)
        self.ui.TestEnvResultlabel.setHidden(True)
        self.ui.progressBarInstallation.setHidden(True)
        self.ui.CreateEnvprogressBar.setHidden(True)
        self.ui.resultDeleteLabel.setHidden(True)
        self.ui.labelDetectionMac.setHidden(True)

        self.ui.lineEditLib.setPlaceholderText('vtk,itk,...')



        self.restoreCondaPath()

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def detectionMac(self):
        self.ui.labelDetectionMac.setHidden(False)

        self.ui.buttonCondaFolder.setEnabled(False)
        self.ui.folderInstallButton.setEnabled(False)
        self.ui.installButton.setEnabled(False)
        self.ui.TestEnvButton.setEnabled(False)
        self.ui.CreateEnvButton.setEnabled(False)
        self.ui.deletePushButton.setEnabled(False)





    def checkboxChangeWsl(self):
        '''
        Check if wsl and Ubuntu are available. If so, change the name of the labels/buttons
        '''
        if self.ui.checkBoxWsl.isChecked():
            if self.conda_wsl.testWslAvailable():
                if self.conda_wsl.testUbuntuAvailable():
                    self.ui.label_1.setText("Miniconda/Anaconda Path in WSL :")
                    self.ui.folderInstallLabel.setText("Folder install in WSL: ")
                    self.ui.installButton.setText("Installation in WSL")
                    self.ui.label_2.setText("Test if environment exist in WSL: ")
                    self.ui.label_2.setStyleSheet("text-decoration: underline;")
                    self.ui.label_3.setText("Create environment in WSL :")
                    self.ui.label_3.setStyleSheet("text-decoration: underline;")
                    self.ui.label_6.setText("Delete environment in WSL :")
                    self.ui.label_6.setStyleSheet("text-decoration: underline;")
                    self.ui.folderInstallLineEdit.setText("")
                else :
                    slicer.util.infoDisplay("There is no Ubuntu distribution on WSL. You can install it here :\nhttps://github.com/DCBIA-OrthoLab/SlicerAutomatedDentalTools/releases/tag/wsl2_windows",windowTitle="Ubuntu not install")
                    self.ui.checkBoxWsl.setChecked(False)

            else :
                slicer.util.infoDisplay("WSL not install. You can install it here :\nhttps://github.com/DCBIA-OrthoLab/SlicerAutomatedDentalTools/releases/tag/wsl2_windows",windowTitle="WSL not install")
                self.ui.checkBoxWsl.setChecked(False)

        else :
            self.ui.label_1.setText("Miniconda/Anaconda Path :")
            self.ui.folderInstallLabel.setText("Folder install : ")
            self.ui.installButton.setText("Installation")
            self.ui.label_2.setText("Test if environment exist : ")
            self.ui.label_2.setStyleSheet("text-decoration: underline;")
            self.ui.label_3.setText("Create environment :")
            self.ui.label_3.setStyleSheet("text-decoration: underline;")
            self.ui.label_6.setText("Delete environment :")
            self.ui.label_6.setStyleSheet("text-decoration: underline;")
            self.ui.folderInstallLineEdit.setText("")
        self.restoreCondaPath()


    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.
        pass


    def setParameterNode(self, inputParameterNode: Optional[CondaSetUpParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()


    def windows_to_linux_path(self,windows_path):
            '''
        Convert a windows path to a path that wsl can read
        '''
            windows_path = windows_path.strip()

            path = windows_path.replace('\\', '/')

            if ':' in path:
                drive, path_without_drive = path.split(':', 1)
                path = "/mnt/" + drive.lower() + path_without_drive

            return path

    def chooseCondaFolder(self):
        '''
        Opens a dialog for selecting a Conda folder, either through a file manager widget (if WSL is used) or a standard folder dialog, and sets the chosen folder in a line edit.
        '''
        surface_folder=False
        if self.ui.checkBoxWsl.isChecked():

            fileManager = FileManagerWidget()
            fileManager.exec_()

            surface_folder = fileManager.getChoosePath()
            user_name = fileManager.getUserName()
            self.conda_wsl.setUser(user_name)
        else :
            slicer_dir = os.path.dirname(slicer.app.slicerHome)
            surface_folder = QFileDialog.getExistingDirectory(self.parent, "Select a scan folder",slicer_dir)

        self.ui.lineEditPathFolder.setText(surface_folder)
        if surface_folder:
            if self.ui.checkBoxWsl.isChecked() :
                self.conda_wsl.setConda(surface_folder)
            else :
                self.conda.setConda(surface_folder)

    def chooseInstallFolder(self):
        '''
        Opens a dialog for selecting a installation folder, either through a file manager widget (if WSL is used) or a standard folder dialog, and sets the chosen folder in a line edit.
        '''
        if self.ui.checkBoxWsl.isChecked():
            fileManager = FileManagerWidget()
            fileManager.exec_()
            # surface_folder = QFileDialog.getExistingDirectory(self.parent, "Select a scan folder",default_path)
            surface_folder = fileManager.getChoosePath()
            print("surface_folder : ",surface_folder)
            user_name = fileManager.getUserName()
            self.conda_wsl.setUser(user_name)
        else :
            slicer_dir = os.path.dirname(slicer.app.slicerHome)
            if platform.system() == 'Darwin':
                surface_folder=os.path.join(slicer_dir, 'Contents', 'lib')
            else:
                surface_folder = QFileDialog.getExistingDirectory(self.parent, "Select a scan folder",slicer_dir)
            self.ui.folderInstallLineEdit.setText(surface_folder)

    def installMiniconda(self):
        '''
        Initiates the installation of Miniconda in the selected folder. It handles both WSL and standard environments, displays installation progress, and updates the UI elements accordingly.
        '''
        if os.path.isdir(self.ui.folderInstallLineEdit.text) or self.ui.checkBoxWsl.isChecked():
            self.ui.timeInstallation.setHidden(False)
            self.ui.timeInstallation.setText("time : 0s")
            dir_path = os.path.dirname(os.path.realpath(__file__))
            name_file = os.path.join(dir_path, "tempo.txt")
            with open(name_file, "w") as fichier:
                    fichier.write("0\n")

            original_stdin = sys.stdin
            sys.stdin = DummyFile()
            original_stdin = sys.stdin
            sys.stdin = DummyFile()
            if self.ui.checkBoxWsl.isChecked() :
                process = threading.Thread(target=self.conda_wsl.installConda, args=(self.ui.folderInstallLineEdit.text,name_file,True))
            else :
                process = threading.Thread(target=self.conda.installConda, args=(self.ui.folderInstallLineEdit.text,name_file,True))
            process.start()
            line = "Start"
            self.ui.progressBarInstallation.setHidden(False)
            start_time = time.time()
            previous_time = time.time()
            current_time = time.time()

            while process.is_alive():
                    with open(name_file, "r") as fichier:
                        line = fichier.read()
                    if "end" in line:
                        print("line : ",line)
                        break
                    else:
                        slicer.app.processEvents()
                        line.replace("\n","")
                        try :
                            self.ui.progressBarInstallation.setValue(int(line))
                            self.ui.progressBarInstallation.setFormat(f"{int(line)}%")
                        except :
                            pass
                    current_time = time.time()
                    if current_time-previous_time > 0.3 :
                        previous_time = current_time
                        self.ui.timeInstallation.setText(f"time : {current_time-start_time:.1f}s")

            with open(name_file, "r") as fichier:
                line = fichier.read()
            if "end" in line:
                print("line : ",line)
                os.remove(name_file)

            folder = self.ui.folderInstallLineEdit.text
            if self.ui.checkBoxWsl.isChecked() :
                self.conda_wsl.setConda(folder+"/miniconda3")
            else :
                # print("os.path.join(folder,miniconda3) : ",os.path.join(folder,"miniconda3"))
                # self.conda.setConda(os.path.join(folder,"miniconda3"))
                self.conda.setConda(folder+"/miniconda3")

            self.restoreCondaPath()

            sys.stdin = original_stdin
            QTimer.singleShot(10000,lambda: self.hideResultLabel("installMiniconda"))



    def createEnv(self):
        '''
        Creates a new Conda environment with specified parameters (like Python version and libraries). It updates the progress bar and handles both WSL and non-WSL environments.
        '''
        name = self.ui.lineEdit_nameEnv.text
        if name :
            python_version = self.ui.lineEditPythonVersion.text
            if python_version :
                lib_list = self.ui.lineEditLib.text
                if lib_list :
                    lib_list = lib_list.split(',')
                else :
                    lib_list = []
                print("lib_list : ",lib_list)
                name_file = "tempo.txt"
                original_stdin = sys.stdin
                sys.stdin = DummyFile()
                if self.ui.checkBoxWsl.isChecked() :
                    process = threading.Thread(target=self.conda_wsl.condaCreateEnv, args=(name,"3.9",lib_list,name_file,True,))
                else :
                    process = threading.Thread(target=self.conda.condaCreateEnv, args=(name,"3.9",lib_list,name_file,True,))
                with open(name_file, "w") as fichier:
                    fichier.write("0\n")
                line = "Start"
                progress = 0
                process.start()
                self.ui.CreateEnvprogressBar.setHidden(False)
                start_time = time.time()
                previous_time = time.time()
                current_time = time.time()
                self.ui.CreateEnvprogressBar.setFormat("0% time : 0s")
                work = False
                while process.is_alive():
                    with open(name_file, "r") as fichier:
                        line = fichier.read()
                    if "end" in line:
                        print("line : ",line)
                        # os.remove(name_file)
                        work = True
                        break
                    elif "Path to conda no setup" in line:
                        print("line : ",line)
                        os.remove(name_file)
                        break
                    else:
                        slicer.app.processEvents()
                        line.replace("\n","")
                        try :
                            self.ui.CreateEnvprogressBar.setValue(int(line))
                            progress = int(line)
                            self.ui.CreateEnvprogressBar.setFormat(f"{progress}% time : {current_time-start_time:.1f}s")
                        except :
                            pass
                    current_time = time.time()
                    if current_time-previous_time > 0.3 :
                        self.ui.CreateEnvprogressBar.setFormat(f"{progress}% time : {current_time-start_time:.1f}s")
                        previous_time = current_time


                with open(name_file, "r") as fichier:
                        line = fichier.read()
                if "end" in line:
                    print("line : ",line)
                    os.remove(name_file)
                    work = True

                if work :
                    self.ui.CreateEnvprogressBar.setValue(100)
                    self.ui.CreateEnvprogressBar.setFormat(f"100%")
                else :
                    self.ui.CreateEnvprogressBar.setValue(0)
                    self.ui.CreateEnvprogressBar.setFormat(f"Path to conda no setup")
                    slicer.util.infoDisplay("Enter a path into 'Miniconda/Anaconda Path'",windowTitle="Can't found conda path")
                sys.stdin = original_stdin
                QTimer.singleShot(10000,lambda: self.hideResultLabel("createEnv"))


    def deleteEnv(self):
        '''
        Deletes a specified Conda environment, updating the UI with the result of the operation, including success, failure, or path-not-found messages.
        '''
        self.ui.resultDeleteLabel.setHidden(True)
        name = self.ui.deleteLineEdit.text
        if name :
            if self.ui.checkBoxWsl.isChecked():
                result = self.conda_wsl.condaDeleteEnv(name)
            else :
                result = self.conda.condaDeleteEnv(name)

            self.ui.resultDeleteLabel.setHidden(False)
            if result == "Delete":
                self.ui.resultDeleteLabel.setText(f"Environment {name} delete succesfully")
                self.ui.resultDeleteLabel.setStyleSheet("color: green;")
            elif result == "Not exist":
                self.ui.resultDeleteLabel.setText(f"The environment {name} doesn't exist")
                self.ui.resultDeleteLabel.setStyleSheet("color: red;")
            elif result == "Path to conda no setup":
                self.ui.resultDeleteLabel.setText(f"Path to conda no setup")
                self.ui.resultDeleteLabel.setStyleSheet("color: red;")
                slicer.util.infoDisplay("Enter a path into 'Miniconda/Anaconda Path'",windowTitle="Can't found conda path")
            else :
                self.ui.resultDeleteLabel.setText(f"An error occured")
                self.ui.resultDeleteLabel.setStyleSheet("color: red;")

            QTimer.singleShot(10000, lambda:self.hideResultLabel("deleteEnv"))



    def restoreCondaPath(self):
        '''
        Sets the current Conda path in a line edit, differentiating between WSL and non-WSL environments.
        '''
        if self.ui.checkBoxWsl.isChecked():
            condaPath = self.conda_wsl.getCondaPath()
        else :
            condaPath = self.conda.getCondaPath()

        self.ui.lineEditPathFolder.setText(condaPath)

    def testEnv(self):
        '''
        Tests if a specified Conda environment exists and updates the UI with the result, including the existence of the environment or a path-not-found error.
        '''
        self.ui.TestEnvResultlabel.setHidden(True)
        name = self.ui.TestEnvlineEdit.text
        if name :
            if self.ui.checkBoxWsl.isChecked():
                result = self.conda_wsl.condaTestEnv(name)
            else :
                result = self.conda.condaTestEnv(name)
            self.ui.TestEnvResultlabel.setHidden(False)
            if result == "Path to conda no setup":
                self.ui.TestEnvResultlabel.setStyleSheet("color: red;")
                self.ui.TestEnvResultlabel.setText(f"Path to conda no setup")
                slicer.util.infoDisplay("Enter a path into 'Miniconda/Anaconda Path'",windowTitle="Can't found conda path")

            elif result :
                self.ui.TestEnvResultlabel.setStyleSheet("color: green;")
                self.ui.TestEnvResultlabel.setText(f"The environment {name} exists.")
            else :
                self.ui.TestEnvResultlabel.setStyleSheet("color: red;")
                self.ui.TestEnvResultlabel.setText(f"The environment {name} doesn't exist.")
        QTimer.singleShot(10000,lambda: self.hideResultLabel("testEnv"))


    def hideResultLabel(self,name_label):
        """
        Hides the Result Label or progress bar
        """
        if name_label=="testEnv" :
            self.ui.TestEnvResultlabel.setHidden(True)

        elif name_label=="deleteEnv":
            self.ui.resultDeleteLabel.setHidden(True)

        elif name_label=="createEnv":
            self.ui.CreateEnvprogressBar.setHidden(True)

        elif name_label=="installMiniconda":
            self.ui.progressBarInstallation.setHidden(True)
            self.ui.timeInstallation.setHidden(True)





class CondaSetUpCallWsl():
    '''
    class for managing Conda environments within a Windows Subsystem for Linux (WSL) context, including installation, environment creation, deletion, and running Python scripts.
    '''

    def __init__(self) -> None:
        '''
        Initializes the class with settings specific to Conda and WSL.
        '''
        self.settings = QSettings("SlicerCondaWSL")

    def testWslAvailable(self):
        '''
        Checks if WSL is available on the system.
        '''
        try:
            result = subprocess.run(["wsl", "--status"], capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            return False
        except FileNotFoundError:
            return False

    def testUbuntuAvailable(self):
        '''
        Verifies if Ubuntu is installed on WSL.
        '''
        result = subprocess.run(['wsl', '--list'], capture_output=True, text=True)
        output = result.stdout.encode('utf-16-le').decode('utf-8')
        clean_output = output.replace('\x00', '')

        return 'Ubuntu' in clean_output

    def getCondaPath(self):
        '''
        Retrieves the stored path of the Conda installation.
        '''
        condaPath = self.settings.value("condaPath", "")
        return condaPath

    def setUser(self,user):
        '''
        Sets the WSL user in the settings.
        '''
        if user :
            self.settings.setValue("user", user)
            print("USER : ",user)

    def setConda(self,pathConda):
        '''
        Sets the path of the Conda installation and related executables in the settings.
        '''
        if pathConda:
            self.settings.setValue("condaPath", pathConda)
            self.settings.setValue("conda/executable",self.settings.value("condaPath", "")+"/bin/conda")
            self.settings.setValue("python3",self.settings.value("condaPath", "")+"/bin/python3")
            self.settings.setValue("activate/executable",pathConda+"/bin/activate")

    def getCondaExecutable(self):
        '''
        Returns the path to the Conda executable.
        '''
        condaExe = self.settings.value("conda/executable", "")
        if condaExe:
            return (condaExe)
        return "None"


    def getUser(self):
        '''
        Gets the WSL user from the settings.
        '''
        return self.settings.value("user","")

    def getActivateExecutable(self):
        '''
        Provides the path to the Conda 'activate' script.
        '''
        ActivateExe = self.settings.value("activate/executable", "")
        if ActivateExe:
            return (ActivateExe)
        return "None"

    def writeFile(self,name_file,text):
        '''
        Writes text to a specified file.
        '''
        with open(name_file, "w") as file:
            file.write(f"{text}\n")

    def installConda(self,folder:str,file_name:str="tempo.txt",writeProgress:bool=False):
        '''
        Installs Miniconda in a specified folder in WSL.
        '''
        try:

            user = self.getUser()
            print("user : ",user)
            command = ["wsl", "--user", user, "--" ,"bash", "-c", f"wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /home/{user}/miniconda.sh && chmod +x /home/{user}/miniconda.sh && bash /home/{user}/miniconda.sh -b -p {folder}/miniconda3 && rm /home/{user}/miniconda.sh && echo 'export PATH=\"{folder}/miniconda3/bin:\\$PATH\"' >> /home/{user}/.bashrc"]
            print("command : ", command)

            subprocess.check_call(command)
            if writeProgress : self.writeFile(file_name,"100")

            print ("Miniconda has been successfully installed on WSL.")
            if writeProgress : self.writeFile(file_name,"end")

        except subprocess.CalledProcessError as e:
            print (f"An error occurred when installing Miniconda on WSL: {e}")

    def condaCreateEnv(self,name,python_version,list_lib=[],tempo_file="tempo.txt",writeProgress=False):
        '''
        Creates a new Conda environment with the given name and Python version, and installs specified libraries.
        '''
        user = self.getUser()
        conda_path = self.getCondaExecutable()
        command_to_execute = ["wsl", "--user", user,"--","bash","-c", f"{conda_path} create -y -n {name} python={python_version} pip numpy-base"]
        if writeProgress : self.writeFile(tempo_file,"20")
        print("command to execute : ",command_to_execute)
        result = subprocess.run(command_to_execute, text=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE,env = slicer.util.startupEnvironment())
        if result.returncode==0:
            print("Execution Successfull")
            self.condaInstallLibEnv(name,list_lib)
        else :
            print("error : ",result.stderr)

        if writeProgress : self.writeFile(tempo_file,"100")
        if writeProgress : self.writeFile(tempo_file,"end")

    def condaInstallLibEnv(self,name,requirements: list[str]):
        '''
        Installs a list of libraries in a specified Conda environment.
        '''
        print("requirements : ",requirements)
        path_activate = self.getActivateExecutable()
        path_conda = self.getCondaPath()
        user = self.getUser()
        if path_activate=="None":
                return "Path to conda no setup"
        else :
            if len(requirements)!=0 :

                command = f"source {path_activate} {name} && pip install"

                for lib in requirements :
                    command = command+ " "+lib
                command_to_execute = ["wsl", "--user", user,"--","bash","-c", command]
                print("command to execute in intsallLib wsl : ",command_to_execute)
                result = subprocess.run(command_to_execute, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', env=slicer.util.startupEnvironment())
                if result.returncode==0:
                    print(f"Result : {result.stdout}")
                    return (f"Result : {result.stdout}")
                else :
                    print(f"Error : {result.stderr}")
                    return (f"Error : {result.stderr}")
            return "Nothing to install"

    def condaDeleteEnv(self,name:str):
        '''
        Deletes a specified Conda environment.
        '''
        exist = self.condaTestEnv(name)
        user = self.getUser()
        if exist:
            path_conda = self.getCondaExecutable()
            if path_conda=="None":
                return "Path to conda no setup"
            command = f"{path_conda} env remove --name {name}"
            command_to_execute = ["wsl", "--user", user,"--","bash","-c", command]
            print("command_to_execute : ",command_to_execute)
            result = subprocess.run(command_to_execute, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=slicer.util.startupEnvironment())
            if result.returncode == 0:
                return "Delete"
            else :
                print(result.stderr)
                return "Error"
        return "Not exist"

    def condaTestEnv(self,name:str)->bool:
        '''
        Checks if a specified Conda environment exists.
        '''

        path_conda = self.getCondaExecutable()
        user = self.getUser()
        if path_conda=="None":
                return "Path to conda no setup"

        command = f"{path_conda} info --envs"
        command_to_execute = ["wsl", "--user", user,"--","bash","-c", command]
        print("command_to_execute : ",command_to_execute)
        result = subprocess.run(command_to_execute, stdout=subprocess.PIPE, stderr=subprocess.PIPE,env = slicer.util.startupEnvironment())
        if result.returncode == 0:
            output = result.stdout.decode("utf-8")
            env_lines = output.strip().split("\n")

            for line in env_lines:
                env_name = line.split()[0].strip()
                if env_name == name:
                    return True
        return False

    def windows_to_linux_path(self,windows_path):
        '''
        Converts a Windows file path to a WSL-compatible path.
        '''
        windows_path = windows_path.strip()

        path = windows_path.replace('\\', '/')

        if ':' in path:
            drive, path_without_drive = path.split(':', 1)
            path = "/mnt/" + drive.lower() + path_without_drive

        return path

    def condaRunFilePython(self, file_path,env_name="None",args=[]):
        '''
        Runs a Python script in a specified Conda environment within WSL.
        '''
        path_condaexe = self.getCondaExecutable()
        path_conda = self.getCondaPath()
        user = self.getUser()

        if env_name!="None":
            if not self.condaTestEnv(env_name):
                return (f"Environnement {env_name} doesn't exist")

        if env_name!="None":
            python_path = path_conda+"/envs/"+env_name+"/bin/python3"
        else :
            python_path = path_conda+"/bin/python3"

        command2 = f"\"{python_path}\""
        if "/mnt/" not in file_path :
            file_path = self.windows_to_linux_path(file_path)
        command2 = command2 +" "+"\""+file_path+"\""

        for arg in args :
            command2 = command2 +" "+"\""+arg+"\""

        command_to_execute = ["wsl", "--user", user,"--","bash","-c", command2]
        print("command_to_execute : ",command_to_execute)

        result = subprocess.run(command_to_execute, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=slicer.util.startupEnvironment())
        if result.returncode == 0:
            return (f"Result: {result.stdout}")
        else :
            return (f"Error: {result.stderr}")

    def condaRunCommand(self, command: list[str],env_name="None"):
        '''
        Executes a command in a specified Conda environment within WSL.
        '''
        path_activate = self.getActivateExecutable()
        user = self.getUser()
        if path_activate=="None":
            return "Path to conda no setup"

        if env_name == "None":
            command_execute=""
        else :
            command_execute = f"source {path_activate} {env_name} &&"
        for com in command :
            command_execute = command_execute+ " "+com

        command_to_execute = ["wsl", "--user", user,"--","bash","-c", command_execute]
        print("command_to_execute in condaRunCommand : ",command_to_execute)
        result = subprocess.run(command_to_execute, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', env=slicer.util.startupEnvironment())
        if result.returncode == 0:
            return (f"Result: {result.stdout}")
        else :
            return (f"Error: {result.stderr}")


class CondaSetUpCall():
    def __init__(self) -> None:
        '''
        Initializes the class and sets up QSettings for Conda configurations.
        '''
        self.settings = QSettings("SlicerConda")

    def convert_path(self,unix_path):
        '''
        Converts a Unix-style path to a Windows-style path.
        '''
        windows_path = unix_path.replace('/', '\\')
        return windows_path

    def setConda(self,pathConda):
        '''
        Sets the Conda installation path and updates related executable paths in the settings based on the operating system.
        '''
        if pathConda:
            self.settings.setValue("condaPath", pathConda)
            if platform.system()=="Windows":
                self.settings.setValue("conda/executable", os.path.join(self.convert_path(pathConda),"Scripts","conda"))
                self.settings.setValue("activate/executable",os.path.join(self.convert_path(pathConda),"Scripts","activate"))
            else :
                self.settings.setValue("conda/executable",os.path.join(self.settings.value("condaPath", ""),"bin","conda"))
                self.settings.setValue("activate/executable",os.path.join(pathConda,"bin","activate"))

    def getCondaExecutable(self):
        '''
        Retrieves the path to the Conda executable from the settings.
        '''
        condaExe = self.settings.value("conda/executable", "")
        if condaExe:
            return (condaExe)
        return "None"

    def getActivateExecutable(self):
        '''
        Gets the path to the Conda 'activate' script from the settings.
        '''
        ActivateExe = self.settings.value("activate/executable", "")
        if ActivateExe:
            return (ActivateExe)
        return "None"

    def getCondaPath(self):
        '''
        Returns the stored Conda installation path from the settings.
        '''
        condaPath = self.settings.value("condaPath", "")
        if condaPath:
            return (condaPath)
        return "None"

    def condaTestEnv(self,name:str)->bool:
        '''
       Checks if a specified Conda environment exists and returns a boolean indicating the result.
        '''

        path_conda = self.getCondaExecutable()
        if path_conda=="None":
                return "Path to conda no setup"

        command_to_execute = [path_conda, "info", "--envs"]

        result = subprocess.run(command_to_execute, stdout=subprocess.PIPE, stderr=subprocess.PIPE,env = slicer.util.startupEnvironment())
        if result.returncode == 0:
            output = result.stdout.decode("utf-8")
            env_lines = output.strip().split("\n")

            for line in env_lines:
                env_name = line.split()[0].strip()
                if env_name == name:
                    return True
        return False

    def installConda(self,path_install:str,name_tempo:str="tempo.txt",writeProgress:bool=False)->None:
        '''
        Installs Conda in a specified path, handling different operating systems and architectures, and optionally updates the installation progress.
        '''
        path_install = os.path.join(path_install,"miniconda3")
        system = platform.system()
        machine = platform.machine()

        miniconda_base_url = "https://repo.anaconda.com/miniconda/"

        # Construct the filename based on the operating system and architecture
        if system == "Windows":
            if machine.endswith("64"):
                filename = "Miniconda3-latest-Windows-x86_64.exe"
            else:
                filename = "Miniconda3-latest-Windows-x86.exe"
        elif system == "Linux":
            if machine == "x86_64":
                filename = "Miniconda3-latest-Linux-x86_64.sh"
            else:
                filename = "Miniconda3-latest-Linux-x86.sh"
        elif system == 'Darwin':
            if machine ==  "x86_64":
                filename = "Miniconda3-latest-MacOSX-x86_64.sh"
            else:
                filename = "Miniconda3-latest-MacOSX-arm64.sh"
        else:
            raise NotImplementedError(f"Unsupported system: {system} {machine}")

        miniconda_url = miniconda_base_url + filename


        path_sh = os.path.join(path_install,"miniconda.sh")
        path_conda = os.path.join(path_install,"bin","conda")


        if not os.path.exists(path_install):
            os.makedirs(path_install)


        if writeProgress : self.writeFile(name_tempo,"20")

        if system == "Windows":
            try:
                path_install = self.convert_path(path_install)
                path_exe = os.path.join(os.path.expanduser("~"), "tempo")

                os.makedirs(path_exe, exist_ok=True)
                # Define paths for the installer and conda executable
                path_installer = os.path.join(path_exe, filename)
                path_conda = os.path.join(path_install, "Scripts", "conda.exe")
                # Download the Anaconda installer
                urllib.request.urlretrieve(miniconda_url, path_installer)
                print("Installer downloaded successfully.")
                print("Installing Miniconda...")

                # Run the Anaconda installer with silent mode
                print("path_installer : ",path_installer)
                print("path_install : ",path_install)

                install_command = f'"{path_installer}" /InstallationType=JustMe /AddToPath=1 /RegisterPython=0 /S /D={path_install}'

                if writeProgress : self.writeFile(name_tempo,"50")

                subprocess.run(install_command, shell=True)

                if writeProgress : self.writeFile(name_tempo,"70")
                subprocess.run(f"{path_conda} init cmd.exe", shell=True)
                print("Miniconda installed successfully.")
                if writeProgress : self.writeFile(name_tempo,"90")

                try:
                    shutil.rmtree(path_exe)
                    print(f"Folder {path_exe} and its contebt has been successfully deleted.")
                    if writeProgress : self.writeFile(name_tempo,"100")
                except Exception as e:
                    print(f"An Error has occured when deleting folder : {str(e)}")
                    return True
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                return False

        else :
            subprocess.run(f"mkdir -p {path_install}",capture_output=True, shell=True)
            if writeProgress : self.writeFile(name_tempo,"30")
            print(f"curl -L --continue-at - --retry 3 {miniconda_url} -o {path_sh}")
            result = subprocess.run(f"curl -L --continue-at - --retry 3 {miniconda_url} -o {path_sh}", 
                                capture_output=True, shell=True)
            print(result.stdout)
            print(result.stderr)
            if writeProgress : self.writeFile(name_tempo,"50")
            subprocess.run(f"chmod +x {path_sh}",capture_output=True, shell=True)
            if writeProgress : self.writeFile(name_tempo,"60")

            try:
                print(f"bash {path_sh} -b -u -p {path_install}")
                result =subprocess.run(f"bash {path_sh} -b -u -p {path_install}",capture_output=True, shell=True)
                print(result.stdout)
                print(result.stderr)

                if writeProgress : self.writeFile(name_tempo,"80")
                subprocess.run(f"rm -rf {path_sh}",shell=True)
                if writeProgress : self.writeFile(name_tempo,"90")
                subprocess.run(f"{path_conda} init bash",shell=True)
                if writeProgress : self.writeFile(name_tempo,"100")
                return True
            except:
                return (False)

        if writeProgress : self.writeFile(name_tempo,"end")


    def writeFile(self,name_file,text):
        '''
        Writes a given text to a specified file, used for logging and progress tracking.
        '''
        with open(name_file, "w") as file:
            file.write(f"{text}\n")

    def condaCreateEnv(self,name,python_version,list_lib,tempo_file="tempo.txt",writeProgress=False):
        '''
        Creates a new Conda environment with a specified Python version and installs a list of libraries, with an option to update progress.
        '''
        path_conda = self.getCondaExecutable()
        if path_conda=="None":
                if writeProgress : self.writeFile(tempo_file,"Path to conda no setup")
        else :
            if writeProgress : self.writeFile(tempo_file,"10")
            command_to_execute = [path_conda, "create", "--name", name, f"python={python_version}", "-y"]
            print("command_to_execute in conda create env : ",command_to_execute)
            result = subprocess.run(command_to_execute, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=slicer.util.startupEnvironment())

            if writeProgress : self.writeFile(tempo_file,"40")

            self.condaInstallLibEnv(name,list_lib)

            if writeProgress : self.writeFile(tempo_file,"100")
            if writeProgress : self.writeFile(tempo_file,"end")


    def condaInstallLibEnv(self,name,requirements: list[str]):
        '''
        Installs a list of specified libraries in a given Conda environment.
        '''
        print("requirements : ",requirements)
        path_activate = self.getActivateExecutable()
        path_conda = self.getCondaPath()
        path_conda_exe = self.getCondaExecutable()
        if path_activate=="None":
                return "Path to conda no setup"
        else :
            if len(requirements)!=0 :
                if platform.system()=="Windows":
                    path_pip = os.path.join(self.convert_path(path_conda),"envs",name,"Scripts","pip")
                    command = f"{path_conda_exe} run pip install"
                else :
                    command = f"{path_conda_exe} run -n {name} pip install"

                for lib in requirements :
                    command = command+ " "+lib
                result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', env=slicer.util.startupEnvironment())
                if result.returncode==0:
                    print(f"Result : {result.stdout}")
                    return (f"Result : {result.stdout}")
                else :
                    print(f"Error : {result.stderr}")
                    return (f"Error : {result.stderr}")
            return "Nothing to install"


    def condaDeleteEnv(self,name:str):
        '''
        Deletes a specified Conda environment and returns the status of the operation.
        '''
        exist = self.condaTestEnv(name)
        if exist:
            path_conda = self.getCondaExecutable()
            if path_conda=="None":
                return "Path to conda no setup"
            command_to_execute = [path_conda, "env", "remove","--name", name,"-y"]
            print(command_to_execute)
            result = subprocess.run(command_to_execute, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=slicer.util.startupEnvironment())
            if result.returncode == 0:
                return "Delete"
            else :
                print(result.stderr)
                return "Error"
        return "Not exist"

    def condaRunFilePython(self,file_path:str,args=[],env_name="None"):
        '''
        Executes a Python script in a specified Conda environment, compatible with both Windows and Unix-like systems.
        '''
        path_condaexe = self.getCondaExecutable()
        path_conda = self.getCondaPath()

        if path_condaexe=="None":
            return "Path to conda no setup"
        if env_name != "None":
            if not self.condaTestEnv(env_name) :
                return "Env doesn't exist"

        
        # file_path = "\""+file_path+"\""
        file_path = file_path
        if platform.system()=="Windows" :
            if env_name != "None" :
                path_python = "\""+os.path.join(self.convert_path(path_conda),"envs",env_name,"python")+"\""
                command = [path_condaexe, 'run', '-n', env_name, path_python, file_path]
            else :
                path_python = "\""+os.path.join(self.convert_path(path_conda),"python")+"\""
                command = [path_condaexe, 'run', path_python, file_path]

        else :
            if env_name != "None" :
                path_python = os.path.join(path_conda,"envs",env_name,"bin","python3")
                command = [path_condaexe, 'run', '-n', env_name,path_python, file_path]
            else :
                path_python = os.path.join(path_conda,"bin","python3")
                command = [path_condaexe, 'run',  path_python,file_path]

        # print("args : ",args)
        for arg in args:
            # command.append("\""+str(arg)+"\"")
            command.append(str(arg))


        # command.append(argument)


        print("command in condaRunFilePython : ",command)
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=slicer.util.startupEnvironment())
        if result.returncode == 0:
            print(f"Result: {result.stdout}")
            return (f"Result: {result.stdout}")
        else :
            print(f"Error: {result.stderr}")
            return (f"Error: {result.stderr}")

    def condaRunCommand(self,command: list[str],env_name="None"):
        '''
        Runs a command in a specified Conda environment, handling different operating systems.
        '''
        path_activate = self.getActivateExecutable()
        if path_activate=="None":
            return "Path to conda no setup"

        command_execute = f"source {path_activate} {env_name} &&"
        path_conda_exe = self.getCondaExecutable()
        if env_name != "None":
            command_execute = f"{path_conda_exe} run -n {env_name}"
        else :
            command_execute = f"{path_conda_exe} run"
        for com in command :
            command_execute = command_execute+ " "+com

        print("command_execute dans conda run : ",command_execute)
        result = subprocess.run(command_execute, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', env=slicer.util.startupEnvironment(),executable="/bin/bash")
        if result.returncode == 0:
            print(f"Result: {result.stdout}")
            return (f"Result: {result.stdout}")
        else :
            print(f"Error: {result.stderr}")
            return (f"Error: {result.stderr}")






class DummyFile(io.IOBase):
        def close(self):
            pass
#
# CondaSetUpLogic
#


class CondaSetUpLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return CondaSetUpParameterNode(super().getParameterNode())

    def process(self) -> None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        a = 1


#
# CondaSetUpTest
#


class CondaSetUpTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_CondaSetUp1()

    def test_CondaSetUp1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        # self.delayDisplay("Starting the test")

        # # Get/create input data

        # import SampleData

        # registerSampleData()
        # inputVolume = SampleData.downloadSample("CondaSetUp1")
        # self.delayDisplay("Loaded test data set")

        # inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        # self.assertEqual(inputScalarRange[0], 0)
        # self.assertEqual(inputScalarRange[1], 695)

        # threshold = 100

        # # Test the module logic

        # logic = CondaSetUpLogic()

        # Test algorithm with non-inverted threshold


        self.delayDisplay("Test passed")
