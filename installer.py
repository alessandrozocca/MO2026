import os
import sys
import shutil
import importlib


def _has_executable(executable_name):
    """Return True if the executable_name is found in the search path."""
    if executable_name is None:
        return True
    if shutil.which(executable_name) is not None:
        return True
    if os.path.isfile(executable_name):
        return True
    return False


def _has_module(module_name):
    """Return true if the module_name can be imported"""
    if module_name is None:
        return True

    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def _check_available(executable, module):
    """Return True if name is installed."""
    return _has_executable(executable) and _has_module(module)


def found_installation(executable=None, module=None):
    """Print message confirming that package was found, then return True or False."""
    is_available = _check_available(executable, module)
    if is_available:
        name = next(n for n in (executable, module) if n is not None)
        print(f"{name} was previously installed")
    return is_available


def confirm_installation(executable=None, module=None):
    """Confirm package is available after installation."""
    if _check_available(executable, module):
        print("installation successful")
        return True
    else:
        print("installation failed")
        return False


def on_colab():
    """Return True if running on Google Colab."""
    return "google.colab" in sys.modules


def install_condacolab():
    if found_installation("conda"):
        return True

    if on_colab():
        print("Installing condacolab via pip ... ", end="")
        print("Restarting the notebook might be required afterwards ... ", end="")
        os.system("pip install -q condacolab")
        import condacolab

        condacolab.install()
    else:
        print("Can only install condacolab on Google Colab ... ", end="")

    return confirm_installation("conda")


def install_idaes():
    if found_installation("idaes"):
        return True

    print("Installing idaes from idaes_pse via pip ... ", end="")
    os.system("pip install -q idaes_pse")

    return confirm_installation("idaes")


def install_idaes_solvers():
    if install_idaes():
        print("Installing idaes extensions ...")
        if on_colab():
            os.system("idaes get-extensions --to /usr/local/bin/")
        else:
            os.system("idaes get-extensions")

    return True


def install_pyomo():
    if found_installation(module="pyomo"):
        return True

    if on_colab():
        return install_idaes()
    else:
        print("Installing pyomo via conda ...", end="")
        os.system("conda install -y -q -c conda-forge pyomo")

    return confirm_installation(module="pyomo")


def install_glpk():
    if found_installation("glpsol"):
        return True

    if on_colab():
        print("Installing glpk on Google Colab via apt-get ... ", end="")
        os.system("apt-get install -y -qq glpk-utils")
    else:
        print("Installing glpk via conda ... ", end="")
        os.system("conda install -y -q -c conda-forge glpk")

    return confirm_installation("glpsol")


def install_ipopt():
    if found_installation("ipopt"):
        return True

    if on_colab():
        return install_idaes_solvers()
    else:
        print("Installing Ipopt via conda ... ", end="")
        os.system("conda install -y -q -c conda-forge ipopt")

    return confirm_installation("ipopt")


def install_cbc():
    if found_installation("cbc"):
        return True

    if on_colab():
        return install_idaes_solvers()
    else:
        print("Installing cbc via apt-get ... ", end="")
        os.system("apt-get install -y -qq coinor-cbc")

    return confirm_installation("cbc")


def install_bonmin():
    if found_installation("bonmin"):
        return True

    if on_colab():
        return install_idaes_solvers()
    else:
        print("No procedure implemented to install bonmin ... ", end="")
        print("You may try to use install_idaes_solvers() instead ... ", end="")

    return confirm_installation("bonmin")


def install_couenne():
    if found_installation("couenne"):
        return True

    if on_colab():
        return install_idaes_solvers()
    else:
        print("No procedure implemented to install couenne ... ", end="")
        print("You may try to use install_idaes_solvers() instead ... ", end="")

    return confirm_installation("couenne")


def install_gecode():
    if found_installation("gecode"):
        return True

    if on_colab():
        print("No procedure implemented to install gecode ... ", end="")
    else:
        print("No procedure implemented to install gecode ... ", end="")

    return confirm_installation("gecode")


def install_scip():
    if found_installation("scip"):
        return True

    print("Installing scip via conda ... ", end="")
    if on_colab():
        install_condacolab()
    os.system("conda install -y -q pyscipopt")

    return confirm_installation("scip")


def install_highs():
    if found_installation(module="highspy"):
        return True

    print("Installing highs via pip ... ", end="")
    os.system("pip install -q highspy")

    return confirm_installation(module="highspy")


def install_gurobi():
    if found_installation(module="gurobipy"):
        return True

    if on_colab():
        print(
            "Installing gurobi on Google Colab via pip (without license) ... ", end=""
        )
        os.system("pip install -q gurobipy")
    else:
        print("Installing gurobi via conda (without license) ... ", end="")
        os.system("conda install -y -q -c gurobi gurobi")

    return confirm_installation(module="gurobipy")


def install_cplex():
    if found_installation(module="cplex"):
        return True

    if on_colab():
        print("Installing cplex on Google Colab via pip (without license) ... ", end="")
        os.system("pip install -q cplex")
    else:
        print("Installing cplex via conda (without license) ... ", end="")
        os.system("conda install -y -q -c ibmdecisionoptimization cplex")

    return confirm_installation(module="cplex")


def install_mosek():
    if found_installation(module="mosek.fusion"):
        return True

    if on_colab():
        print("Installing mosek on Google Colab via pip (without license) ... ", end="")
        os.system("pip install -q mosek")
    else:
        print("Installing mosek via conda  (without license) ... ", end="")
        os.system("conda install -y -q -c mosek mosek")

    return confirm_installation(module="mosek.fusion")


def install_xpress():
    if found_installation(module="xpress"):
        return True

    if on_colab():
        print(
            "Installing xpress on Google Colab via pip (without license) ... ", end=""
        )
        os.system("pip install -q xpress")
    else:
        print("Installing xpress via conda (without license) ... ", end="")
        os.system("conda install -y -q -c fico-xpress xpress")

    return confirm_installation(module="xpress")
