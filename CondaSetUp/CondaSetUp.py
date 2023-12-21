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
import platform
import qt
import subprocess
import shutil
import urllib
import multiprocessing
# from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog
# from PyQt5.QtCore import QSettings
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

        self.ui.outputsCollapsibleButton.setText("Installation miniconda3")

        # Buttons
        self.ui.buttonCondaFolder.connect("clicked(bool)", self.chooseCondaFolder)
        self.ui.TestEnvButton.connect("clicked(bool)", self.testEnv)
        self.ui.folderInstallButton.connect("clicked(bool)", self.chooseInstallFolder)
        self.ui.installButton.connect("clicked(bool)", self.installMiniconda)
        self.ui.CreateEnvButton.connect("clicked(bool)", self.createEnv)
        self.ui.deletePushButton.connect("clicked(bool)",self.deleteEnv)

        #Hidden
        self.ui.TestEnvResultlabel.setHidden(True)
        self.ui.progressBarInstallation.setHidden(True)
        self.ui.CreateEnvprogressBar.setHidden(True)
        self.ui.resultDeleteLabel.setHidden(True)

        self.ui.lineEditLib.setPlaceholderText('vtk,itk,...')

        # Restaurer le chemin sauvegardé (si disponible)
        self.restoreCondaPath()

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

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


    def chooseCondaFolder(self):
        surface_folder = qt.QFileDialog.getExistingDirectory(self.parent, "Select a scan folder")
        self.ui.lineEditPathFolder.setText(surface_folder)
        if surface_folder:
            self.conda.setConda(surface_folder)

    def chooseInstallFolder(self):
        surface_folder = qt.QFileDialog.getExistingDirectory(self.parent, "Select a scan folder")
        self.ui.folderInstallLineEdit.setText(surface_folder)

    def installMiniconda(self):
        if os.path.isdir(self.ui.folderInstallLineEdit.text):
            name_file = "tempo.txt"
            with open(name_file, "w") as fichier:
                    fichier.write("0\n")

            original_stdin = sys.stdin
            sys.stdin = DummyFile()
            process = multiprocessing.Process(target=self.conda.installConda, args=(self.ui.folderInstallLineEdit.text,name_file,True))
            process.start()
            line = "Start"
            self.ui.progressBarInstallation.setHidden(False)

            while "end" not in line:
                with open(name_file, "r") as fichier:
                    line = fichier.read()
                if "end" in line:
                    os.remove(name_file)
                    break
                else:
                    slicer.app.processEvents()
                    line.replace("\n","")
                    try : 
                        self.ui.progressBarInstallation.setValue(int(line))
                        self.ui.progressBarInstallation.setFormat(f"{int(line)}%")
                    except : 
                        pass

            sys.stdin = original_stdin

        
    def createEnv(self):
        name = self.ui.lineEdit_nameEnv.text
        if name :
            python_version = self.ui.lineEditPythonVersion.text
            if python_version :
                lib_list = self.ui.lineEditLib.text
                if lib_list : 
                    lib_list = lib_list.split(',')
                else : 
                    lib_list = []
                name_file = "tempo.txt"
                original_stdin = sys.stdin
                sys.stdin = DummyFile()
                process = multiprocessing.Process(target=self.conda.condaCreateEnv, args=(name,python_version,lib_list,name_file,True))
                process.start()
                with open(name_file, "w") as fichier:
                    fichier.write("0\n")
                line = "Start"
                self.ui.CreateEnvprogressBar.setHidden(False)
                work = False
                while "end" not in line:
                    with open(name_file, "r") as fichier:
                        line = fichier.read()
                    if "end" in line:
                        os.remove(name_file)
                        work = True
                        break
                    elif "Path to conda no setup" in line:
                        os.remove(name_file)
                        break
                    else:
                        slicer.app.processEvents()
                        line.replace("\n","")
                        try : 
                            self.ui.CreateEnvprogressBar.setValue(int(line))
                            self.ui.CreateEnvprogressBar.setFormat(f"{int(line)}%")
                        except : 
                            pass

                if work :
                    self.ui.CreateEnvprogressBar.setValue(100)
                    self.ui.CreateEnvprogressBar.setFormat(f"100%")
                else : 
                    self.ui.CreateEnvprogressBar.setValue(0)
                    self.ui.CreateEnvprogressBar.setFormat(f"Path to conda no setup")
                    slicer.util.infoDisplay("Enter a path into 'Miniconda/Anaconda Path'",windowTitle="Can't found conda path")
                sys.stdin = original_stdin
                

    def deleteEnv(self):
        self.ui.resultDeleteLabel.setHidden(True)
        name = self.ui.deleteLineEdit.text
        if name : 
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



    def restoreCondaPath(self):
        condaPath = self.conda.getCondaPath()
        if condaPath:
            self.ui.lineEditPathFolder.setText(condaPath)

    def testEnv(self):
        self.ui.TestEnvResultlabel.setHidden(True)
        name = self.ui.TestEnvlineEdit.text
        if name :
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



        


        
    

class CondaSetUpCall():
    def __init__(self) -> None:
        self.settings = qt.QSettings("SlicerConda")

    def setConda(self,pathConda):
        if pathConda:
            self.settings.setValue("condaPath", pathConda)
            if platform.system()=="Windows":
                self.settings.setValue("conda/executable", os.path.join(self.settings.value("condaPath", ""),"Scripts","conda"))
                self.settings.setValue("activate/executable",os.path.join(pathConda,"Scripts","activate"))
            else : 
                self.settings.setValue("conda/executable",os.path.join(self.settings.value("condaPath", ""),"bin","conda"))
                self.settings.setValue("activate/executable",os.path.join(pathConda,"bin","activate"))

    def getCondaExecutable(self):
        condaExe = self.settings.value("conda/executable", "")
        if condaExe:
            return (condaExe)
        return "None"
    
    def getActivateExecutable(self):
        ActivateExe = self.settings.value("activate/executable", "")
        if ActivateExe:
            return (ActivateExe)
        return "None"
    
    def getCondaPath(self):
        condaPath = self.settings.value("condaPath", "")
        if condaPath:
            return (condaPath)
        return "None"
        
    def condaTestEnv(self,name:str)->bool:
        '''
        check if the environnement 'name' exist in miniconda3. return bool
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
        install conda
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
                path_miniconda = os.path.join(path_install,"miniconda")

                # Commande pour une installation silencieuse avec Miniconda
                install_command = f'"{path_installer}" /InstallationType=JustMe /AddToPath=1 /RegisterPython=0 /S /D={path_install}'

                if writeProgress : self.writeFile(name_tempo,"50")
                # Exécutez la commande d'installation
                subprocess.run(install_command, shell=True)

                if writeProgress : self.writeFile(name_tempo,"70")
                subprocess.run(f"{path_conda} init cmd.exe", shell=True)
                print("Miniconda installed successfully.")
                if writeProgress : self.writeFile(name_tempo,"90")
                
                try:
                    shutil.rmtree(path_exe)
                    print(f"Dossier {path_exe} et son contenu ont été supprimés avec succès.")
                    if writeProgress : self.writeFile(name_tempo,"100")
                except Exception as e:
                    print(f"Une erreur s'est produite lors de la suppression du dossier : {str(e)}")
                    return True
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                return False

        else : 
            subprocess.run(f"mkdir -p {path_install}",capture_output=True, shell=True)
            if writeProgress : self.writeFile(name_tempo,"30")
            subprocess.run(f"wget --continue --tries=3 {miniconda_url} -O {path_sh}",capture_output=True, shell=True)
            if writeProgress : self.writeFile(name_tempo,"50")
            subprocess.run(f"chmod +x {path_sh}",capture_output=True, shell=True)
            if writeProgress : self.writeFile(name_tempo,"60")

            try:
                subprocess.run(f"bash {path_sh} -b -u -p {path_install}",capture_output=True, shell=True)
                if writeProgress : self.writeFile(name_tempo,"80")
                subprocess.run(f"rm -rf {path_sh}",shell=True)
                if writeProgress : self.writeFile(name_tempo,"90")
                subprocess.run(f"{path_conda} init bash",shell=True)
                if writeProgress : self.writeFile(name_tempo,"100")
                return True
            except:
                print("Le fichier est invalide.")
                return (False)
            
        if writeProgress : self.writeFile(name_tempo,"end")
        

    def writeFile(self,name_file,text):
        with open(name_file, "w") as file:
            file.write(f"{text}\n")

    def condaCreateEnv(self,name,python_version,list_lib,tempo_file="tempo.txt",writeProgress=False):
        path_conda = self.getCondaExecutable()
        if path_conda=="None":
                if writeProgress : self.writeFile(tempo_file,"Path to conda no setup")
        else :
            if writeProgress : self.writeFile(tempo_file,"10")
            command_to_execute = [path_conda, "create", "--name", name, f"python={python_version}", "-y"]  
            result = subprocess.run(command_to_execute, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=slicer.util.startupEnvironment())

            if writeProgress : self.writeFile(tempo_file,"40")

            self.condaInstallLibEnv(name,list_lib)

            if writeProgress : self.writeFile(tempo_file,"100")
            if writeProgress : self.writeFile(tempo_file,"end")

    def condaInstallLibEnv(self,name,requirements: list[str]):
        path_activate = self.getActivateExecutable()
        if path_activate=="None":
                return "Path to conda no setup"
        else :
            command = f"source {path_activate} {name} && pip install"
            for lib in requirements :
                command = command+ " "+lib
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', env=slicer.util.startupEnvironment())
            if result.returncode==0:
                return (f"Result : {result.stdout}")
            else :
                return (f"Error : {result.stderr}")


    def condaDeleteEnv(self,name:str):
        exist = self.condaTestEnv(name)
        if exist:
            path_conda = self.getCondaExecutable()
            if path_conda=="None":
                return "Path to conda no setup"
            command_to_execute = [path_conda, "env", "remove","--name", name]  
            result = subprocess.run(command_to_execute, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=slicer.util.startupEnvironment())
            if result.returncode == 0:
                return "Delete"
            else :
                print(result.stderr)
                return "Error"
        return "Not exist"
    
    def condaRunFile(self,env_name: str, command: list[str]):
        path_conda = self.getCondaExecutable()
        if path_conda=="None":
            return "Path to conda no setup"
        command = [path_conda, 'run', '-n', env_name, *command]
        print("command dans conda run : ",command)
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=slicer.util.startupEnvironment())
        if result.returncode == 0:
            return (f"Result: {result.stdout}")
        else :
            return (f"Error: {result.stderr}")
        
    def condaRunCommand(self,env_name: str, command: list[str]):
        path_activate = self.getActivateExecutable()
        if path_activate=="None":
            return "Path to conda no setup"
        
        command_execute = f"source {path_activate} {env_name} &&"
        for com in command :
            command_execute = command_execute+ " "+com

        print("command_execute dans conda run : ",command_execute)
        result = subprocess.run(command_execute, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', env=slicer.util.startupEnvironment(),executable="/bin/bash")
        if result.returncode == 0:
            return (f"Result: {result.stdout}")
        else :
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

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData

        registerSampleData()
        inputVolume = SampleData.downloadSample("CondaSetUp1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        threshold = 100

        # Test the module logic

        logic = CondaSetUpLogic()

        # Test algorithm with non-inverted threshold
        

        self.delayDisplay("Test passed")
