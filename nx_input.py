"""nx_input.py

Reusable NX Open (Python) helpers for prompting the user for input.

Import and reuse from any journal:

    from nx_input import ask_string

    name = ask_string("Enter the part name:")
    if name is None:
        return  # user left it empty / cancelled

--------------------------------------------------------------------------
NOTE: the AskStringInput buffer gotcha
--------------------------------------------------------------------------
The UF signature is:

    int AskStringInput(string cue, ref string str, out int length)

`str` is a REF BUFFER: the text the user types is written back into the
string you pass in. That buffer must be pre-sized to EXACTLY 133 characters
(UF_UI_MAX_STRING_BUFSIZE = 132 usable chars + a null terminator). Passing
any other length raises "Array length mismatch. Expecting array dimension
133, found array dimension N", and passing "" always returns an empty result
-- e.g. the raw tuple comes back as ('', 0, 8) no matter what the user types.

The fix is to pass exactly 133 spaces and strip the padding off the result.
Python returns the out-params as a tuple in which exactly one element is a
string (the entered text), so we pick it out by type rather than relying on a
fixed position. Note the 132-character limit on what the user can enter.

Second gotcha: AskStringInput silently returns WITHOUT showing a dialog (the
buffer comes back unchanged, e.g. length 132, response 8) unless UI access is
locked around it. Bracket the call with:

    ufs.Ui.LockUgAccess(NXOpen.UF.UFConstants.UF_UI_FROM_CUSTOM)
    ... AskStringInput ...
    ufs.Ui.UnlockUgAccess(NXOpen.UF.UFConstants.UF_UI_FROM_CUSTOM)

The nxopen MCP server does not index NXOpen.UF, so this was confirmed against
the online NX Python API reference:
https://docs.plm.automation.siemens.com/data_services/resources/nx/10/nx_api/en_US/custom/nxopen_python_ref/NXOpen.UF.Ui.AskStringInput.html
"""

import NXOpen
import NXOpen.UF


# UF requires the AskStringInput ref buffer to be exactly this length
# (UF_UI_MAX_STRING_BUFSIZE = 132 usable chars + null terminator).
_UF_STRING_BUFSIZE = 133


def ask_string(message):
    """Prompt the user for a single line of text via the UF input dialog.

    Args:
        message: The prompt shown to the user.

    Returns:
        The entered string, stripped of surrounding whitespace, or None if it
        is left empty. Note the user can enter at most 132 characters.

    Note: `message` (the cue) is NOT shown inside the popup box -- NX displays
    it in the cue/status line at the top or bottom of the graphics window. The
    popup itself only contains the text field. (In-box title/prompt text would
    require a BlockStyler dialog; NXInputBox.GetInputString is VB-only.)
    """
    uf_session = NXOpen.UF.UFSession.GetUFSession()

    # AskStringInput will silently return without ever showing a dialog unless
    # UI access is locked around it. Bracket it with LockUgAccess /
    # UnlockUgAccess(UF_UI_FROM_CUSTOM) so the dialog actually displays.
    uf_session.Ui.LockUgAccess(NXOpen.UF.UFConstants.UF_UI_FROM_CUSTOM)
    try:
        result = uf_session.Ui.AskStringInput(message, " " * _UF_STRING_BUFSIZE)
    finally:
        uf_session.Ui.UnlockUgAccess(NXOpen.UF.UFConstants.UF_UI_FROM_CUSTOM)

    # Only one element of the returned tuple is a string (the entered text).
    strings = [x for x in result if isinstance(x, str)]
    value = strings[0].strip() if strings else ""
    return value or None
