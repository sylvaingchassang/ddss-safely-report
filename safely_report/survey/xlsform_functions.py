from typing import Any
import os
import importlib.util
import random

from flask_login import current_user
from markupsafe import escape

from safely_report.models import Respondent, Role
from safely_report.settings import MEDIA_PATH


class XLSFormFunctions:
    """
    Implement Python counterparts (e.g., `_selected_at()`)
    of XLSForm functions (e.g., `selected-at()`).

    XLSForm functions are listed in the ODK documentation:
    https://docs.getodk.org/form-operators-functions/

    NOTE: These methods are to be inherited and used by
    `SurveyProcessor` to process XLSForm logic, so they need
    to follow consistent naming format (e.g., single leading
    underscore).
    """

    @classmethod
    def _if(cls, condition: bool, then: Any, otherwise: Any) -> Any:
        return then if condition is True else otherwise

    @classmethod
    def _selected(cls, choice_array: list[str], choice: str) -> bool:
        return choice in choice_array

    @classmethod
    def _selected_at(cls, choice_array: list[str], index: int) -> str:
        try:
            return choice_array[index]
        except IndexError:
            return ""

    @classmethod
    def _escape(cls, value: str) -> str:
        return escape(value)

    @classmethod
    def _str2int(cls, value: str) -> int:
        return int(value)

    @classmethod
    def _loadtxt(cls, filename: str) -> str:
        """
        Load the content of a text file located in MEDIA_FOLDER.
        
        Parameters
        ----------
        filename: str
            Name of the text file to load
        
        Returns
        -------
        str
            Content of the text file
        """
        filepath = os.path.join(MEDIA_PATH, filename + ".txt")
        print('FILE PATH', filepath)
        with open(filepath, "r") as file:
            return '\n'.join(file.readlines())
        # TODO:  should raise error if file not found
        

    @classmethod
    def _pulldata(cls, column: str, default: str) -> str:
        """
        Pull data from 'column' in the respondent roster table.

        Parameters
        ----------
        column: str
            Name of the field you want to retrieve
        default: str
            Default value in case the field is not available,
            or the user is an Enumerator

        Returns
        -------
        str
            Field value if available, default otherwise
        """
        if current_user.role != Role.Respondent:
            return default

        respondent_uuid = current_user.uuid
        respondent = Respondent.query.filter_by(uuid=respondent_uuid).first()

        if hasattr(respondent, column):
            return getattr(respondent, column)
        else:
            return default
        
        
    @classmethod
    def _pycall(cls, modulename: str, funcname: str, *args: Any) -> Any:
        """
        Call a Python function by name.

        Parameters
        ----------
        modulename: str
            Name of the module containing the function
        funcname: str
            Name of the function to call
        args: Any
            Arguments to pass to the function

        Returns
        -------
        Any
            Return value of the function
        """
        
        # get function file from MEDIA_PATH
        module_file = os.path.join(MEDIA_PATH, modulename + '.py')
        
        # Create a module specification and load the module
        spec = importlib.util.spec_from_file_location(
            modulename.split('.')[0], module_file)
        print('SPEC', spec)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Get the function from the module
        func = getattr(module, funcname)

        # Call the function with the provided arguments
        return func(*args)
    
        
    @classmethod
    def _randint(cls, low: int, high: int) -> int:
        """
        Generate a random integer between low and high (inclusive).

        Parameters
        ----------
        low: int
            Lower bound of the random integer
        high: int
            Upper bound of the random integer

        Returns
        -------
        int
            Random integer between low and high
        """
        return random.randint(low, high)
