# type: ignore
# flake8: noqa

"""
For monkey-patching some additional magic on top of streamlit
"""

from ast import literal_eval
from datetime import date
from functools import wraps
from typing import Any, Callable

from dateutil import parser
from streamlit import *
from streamlit import __version__


def get_query_params() -> dict:
    """
    When page is first loaded, or if current params are empty, sync url params to
    session state. Afterwards, just return local copy.
    """
    if "raw_query_params" not in session_state or not session_state["raw_query_params"]:
        # Add small delay when first checking the url, before creating the widgets,
        # to handle the case when the query params aren't available yet
        # TODO: Fix this to gracefully handle the case where there really are no
        # query params, so it doesn't wait on every widget on the page
        # sleep(0.2)
        params = experimental_get_query_params()
        session_state["raw_query_params"] = params
    return session_state["raw_query_params"]


def set_query_params(**kwargs):
    """
    Keep local session state up to date with latest widget values, and
    also update url query params to match
    """
    session_state["raw_query_params"].update(
        {
            # Turn all values into a list of strings, since that's the
            # default way they are returned in query params
            key: [str(value)]
            if type(value) not in [tuple, list]
            else [str(v) for v in value]
            for key, value in kwargs.items()
        }
    )
    experimental_set_query_params(**kwargs)


def _get_singleton_query_param(key: str, default: Any = None) -> str:
    """
    Since most of the time, we want a single entry from a query parameter, this just
    returns a single value, rather than a list of 1 item.

    It takes an optional Default value. If it is not provided, and the key is missing
    from the url parameters, it raises a KeyError
    """
    if default is None:
        return get_query_params()[key][0]
    return get_query_params().get(key, [str(default)])[0]


def _string_to_bool(string: str) -> bool:
    """
    Most of the time, it's easy to convert strings to the necessary type (e.g. int,
    float), but this is to handle the special case of converting a string to a bool.
    """
    return string.lower() == "true"


def url_sync(widget: Callable, value_type: type = None, default_value: Any = None):
    @wraps(widget)
    def wrapper(label: str, *args, **kwargs) -> Any:
        """
        Wrapps a streamlit widget, adding a new optional parameter `url_sync`. If it is
        not True, then this simply returns the standard version of the widget

        If url_sync=True, then create a new key for this widget, and use that to keep
        the following in sync:
            * The state of the widget
            * An entry in st.session_state
            * A url parameter
        """
        try:
            url_sync = kwargs.pop("url_sync", False)
            if url_sync == False:
                raise KeyError
        except KeyError:
            return widget(label, *args, **kwargs)

        # Derive widget class from string representation of widget
        # e.g. "<bound method CheckboxMixin.checkbox of..." -> "checkbox"
        widget_type = str(widget).split("Mixin.")[1].split()[0]

        # Make key that will be used in both session state and url param
        sync_key = f"{widget_type}_{label}".replace(" ", "_").lower()

        if widget_type == "multiselect":
            url_param = get_query_params().get(sync_key)
        else:
            try:
                url_param = _get_singleton_query_param(sync_key, default_value)
            except KeyError:
                url_param = None

        if url_param is not None:
            if value_type is bool:
                url_value = _string_to_bool(url_param)
            elif widget_type in ["radio", "selectbox"]:
                options = kwargs.pop("options", args[0])
                url_value = options[int(url_param)]
            elif widget_type == "slider":
                try:
                    url_value = float(url_param)
                except ValueError:
                    try:
                        url_value = parser.parse(url_param)
                    except parser.ParserError:
                        # Handle tuple in case of a range slider
                        url_value = literal_eval(url_param)
            elif widget_type == "date_input":
                url_value = parser.parse(url_param).date()
            elif widget_type == "multiselect":
                url_value = url_param
            elif value_type != str and "(" in url_param:
                url_value = literal_eval(url_param)
            else:
                url_value = value_type(url_param)
        else:
            url_value = None

        if sync_key not in session_state:
            if url_value is not None:
                session_state[sync_key] = url_value
            elif "value" in kwargs:
                session_state[sync_key] = kwargs.pop("value")
            elif "index" in kwargs:
                session_state[sync_key] = kwargs.pop("index")
            elif "default" in kwargs:
                session_state[sync_key] = kwargs.pop("default")

        original_on_change = kwargs.pop("on_change", None)

        def on_change():
            new_value = session_state[sync_key]
            current_params = get_query_params()
            if widget_type in ["radio", "selectbox"]:
                options = kwargs.pop("options", args[0])
                new_index = options.index(new_value)
                current_params.update({sync_key: new_index})
            elif type(new_value) == tuple:
                current_params.update({sync_key: str(new_value)})
            else:
                current_params.update({sync_key: new_value})
            set_query_params(**current_params)

            if original_on_change is not None:
                original_on_change()

        kwargs["on_change"] = on_change

        new_value = widget(label, *args, key=sync_key, **kwargs)

        return new_value

    return wrapper


checkbox = url_sync(checkbox, bool, False)
radio = url_sync(radio, int, 0)
text_input = url_sync(text_input, str, "")
text_area = url_sync(text_area, str, "")
number_input = url_sync(number_input, float)
slider = url_sync(slider)
date_input = url_sync(date_input, date)
selectbox = url_sync(selectbox, int, 0)
multiselect = url_sync(multiselect, list)
