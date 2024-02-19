# SlicerConda

This extension is currently not available on Mac.  
SlicerConda is an extension for efficiently installing and managing Conda environments on Linux, Windows, and Windows Subsystem for Linux (WSL). It simplifies the process of setting up Miniconda and offers straightforward environment management for both users and developers within the Slicer platform.

<p align="center">
    <img src="screenshot/CondaSetUp_icon_big_format.png" alt="View extension on Linux" width="230"/>
</p>


## Features
- Conda Installation: Facilitates Miniconda installation on various operating systems.
- Custom Installation Path: Allows users to select their preferred directory for Miniconda.
- Environment Management: Provides capabilities to create, delete, and verify Conda environments.
- Developer Integration: Includes CondaSetUpCall and CondaSetUpCallWsl classes for advanced Conda operations.
- Script and Command Execution: Enables launching Python scripts and commands in specified Conda environments.

## Using SlicerConda
### For Users
- Setup Conda: After Miniconda installation on Linux/Windows/WSL, enter the path to the Miniconda folder.
- Manage Environments: Utilize SlicerConda's interface to create, delete, or check the existence of Conda environments.
<p align="center">
    <img src="screenshot/Screenshot2.png" alt="View extension on Linux" width="500"/>
</p>

### For Developers
Classes for Manipulation: Use ***CondaSetUpCall*** (for Linux and Windows) or ***CondaSetUpCallWsl*** (for WSL) in your scripts to interact with Conda.
#### Functionalities:
- Retrieve the Miniconda path.
- Create, delete, or test the existence of environments.
- Execute Python files or specific commands in chosen environments.

#### Functions :


| Function name | CondaSetUpCall                   | CondaSetUpCallWsl |
|-----------|------------------------------|-----------|
| getCondaPath | Input : None<br>Output : str | Input : None<br>Output : str |
| getCondaExecutable | Input : None<br>Output : str | Input : None<br>Output : str |
| getActivateExecutable | Input : None<br>Output : str | Input : None<br>Output : str |
| condaTestEnv | Input : name:str<br>Output : bool | Input : name:str<br>Output : bool  |
| condaCreateEnv | Input : name:str,python_version:str,list_lib:[str],tempo_file="tempo.txt",writeProgress=False<br>Output : None | Input : name:str,python_version:str,list_lib=[str],tempo_file="tempo.txt",writeProgress=False<br>Output : str |
| condaInstallLibEnv | Input : name:str,requirements: list[str]<br>Output : str | Input : name:str,requirements: list[str]<br>Output : str |
| condaDeleteEnv | Input : name:str<br>Output : str | Input : name:str<br>Output : str |
| condaRunFilePython | Input : file_path:str,args=[],env_name="None"<br>Output : str | Input : file_path,env_name="None",args=[]<br>Output : str |
| condaRunCommand | Input : env_name: str, command: list[str]<br>Output : str | Input : command: list[str],env_name="None"<br>Output : str |
| getUser | Doesn't exist | Input : None: str<br>Output : str |

## Why use SlicerConda ? : 
Here's a scenario in which you could use this extension highlighting the benefits for both users and developers:  
- **Scenario Introduction**: Shapeaxi, a Python library, cannot be directly installed in Slicer due to version conflicts with existing libraries. It includes a vital feature for teeth segmentation crucial for certain dental imaging modules.
- **Challenge Faced**: Utilizing Shapeaxi requires setting it up in a separate environment because of its incompatibility with Slicer's current library versions.
- **Solution for Users - SlicerConda**:
    - Simplifies installation of Miniconda3 on their systems.
    - Integrates their Miniconda path directly into 3D Slicer.
- **Solution for Developers - SlicerConda**:
    - Facilitates the creation of new environments directly from 3D Slicer to an external environment manager (Miniconda/Anaconda).
    - Allows Shapeaxi to be installed from 3D Slicer into an external environment, guaranteeing its seamless integration into the development process.
    - Allows ShapeAxi to be run from 3D Slicer in an external environment, ensuring smooth workflow integration.


## Example of SlicerConda use for developers :
For a practical demonstration of SlicerConda's capabilities, check out a straightforward example [here](https://github.com/DCBIA-OrthoLab/SlicerConda/blob/main/Example/Example.py#L265C1-L348C69). This particular module is designed for thresholding an image within a specific Conda environment. 
- **Environment Verification**:  The module verifies the existence of the required Conda environment and the module needed for image thresholding.
- **Setup and Installation**: In cases where the environment or module is absent, the module uses SlicerConda,with the user's consent, to automatically configure the environment. It then installs all the components required to facilitate the image thresholding process.  
- **Running** : Using SlicerConda, the module executes a python code to threshold an image in a specific Conda environment.

## Idea for improvements : 
- Make it available on Mac
- Create a button to automatically launch a terminal in a specific environment
