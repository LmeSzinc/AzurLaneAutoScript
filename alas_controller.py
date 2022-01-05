import platform
import os
from subprocess import call
class AlasController:
    def __init__(self):
        self.work_path = os.path.dirname(__file__)
        self.system = platform.system()
        self.repository = "https://github.com/LmeSzinc/AzurLaneAutoScript"
        self.python_path = ""
        self.git_path = ""
        self.check_python()
        self.check_git()
     
    def check_sys(self):
        """
        Determine the system type
        """
        if self.system == "Windows":
            print(self.system)
            pass
        else:
            print("Current OS is not supported")
            quit()
            
    def check_python(self):
        """
        check python
        """
        var_name = "Path"
        toolkit_path = os.path.join(self.work_path,"toolkit")
        
        if os.path.exists(toolkit_path):
            self.python_path = self.python_path = os.path.join(toolkit_path, "python.exe")
        
        elif var_name in os.environ:
            if self.system == "Windows":
                path_list = os.environ[var_name].split(";")
                for path in path_list:
                    if "Python37" in path and "Scripts" not in path:
                        self.python_path = os.path.join(path, "python.exe")
                    else:
                        raise EnvironmentError(
                        f"Python3.7 not found in environment variables :{os.environ[var_name]}")
            else:
                print("Current OS is not supported")
                quit()
        else:
            raise EnvironmentError(
            f"Please configure environment variables")
            
    def check_git(self):
        """
        check git
        """
        var_name = "Path"
        toolkit_path = os.path.join(self.work_path,"toolkit")
        
        if os.path.exists(toolkit_path):
            self.git_path = os.path.join(toolkit_path, "Git\mingw64\\bin\git.exe")
        
        elif var_name in os.environ:
            if self.system == "Windows":
                path_list = os.environ[var_name].split(";")
                for path in path_list:
                    if "Git\mingw64\\bin" in path:
                        self.git_path = os.path.join(path, "git.exe")
                    else:
                        raise EnvironmentError(
                        f"git not found in environment variables :{os.environ[var_name]}")
            else:
                print("Current OS is not supported")
                quit()
        else:
            raise EnvironmentError(
            f"Please configure environment variables")
    def python(self, args):
        return f"{self.python_path} {args}"
    def git(self, args):
        return f"{self.git_path} -C {self.work_path} {args}"
    
    def update(self):
        call(self.git("pull"))
           
    def run(self):
        self.check_sys()
        call(self.python(os.path.join(self.work_path,"gui.py")))
        
# alas = AlasController()
# print(alas.update())


