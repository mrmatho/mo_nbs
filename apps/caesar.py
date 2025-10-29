import marimo

__generated_with = "0.16.5"
app = marimo.App(width="full")


@app.cell
def _(mo):
    mo.md(r"""# Caesar Cipher Testing""")
    return


@app.cell
def _(mo):
    text_box = mo.ui.text(label="Text", value="")
    shift_box = mo.ui.number(label="Shift", value=3, start=-25, stop=25, step=1)
    encrypt = mo.ui.switch(label="Encrypt", value=True)


    def caesar_cipher(text, shift):
        result = ""
        for char in text:
            if char.isalpha():
                shift_base = ord("A") if char.isupper() else ord("a")
                result += chr((ord(char) - shift_base + shift) % 26 + shift_base)
            else:
                result += char
        return result


    def caesar_decipher(text, shift):
        return caesar_cipher(text, -shift)


    mo.hstack([text_box, shift_box, encrypt])
    return caesar_cipher, caesar_decipher, encrypt, shift_box, text_box


@app.cell
def _(caesar_cipher, caesar_decipher, encrypt, mo, shift_box, text_box):
    if encrypt.value:
        out = mo.md("##" + caesar_cipher(text_box.value, shift_box.value))
    else:
        out = mo.md("##" + caesar_decipher(text_box.value, shift_box.value))

    out
    return


@app.cell
def _(caesar_cipher, mo, text_box):
    # Output every possible option in a numbered markdown list
    _out = ""
    for _i in range(1, 26):
        _out += f"1. {caesar_cipher(text_box.value, _i)} \n"

    mo.md(_out)
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
