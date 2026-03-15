import os
import platform
import subprocess


def print_pdf_windows(pdf_path):
    """Print PDF on Windows using multiple methods."""
    pdf_path = os.path.abspath(pdf_path)

    # Method 1: Try using gsprint (Ghostscript) - most reliable for PDF
    try:
        import win32api  # noqa
        import win32print  # noqa

        # Try to find Ghostscript
        gs_paths = [
            r"C:\Program Files\gs\gs*\bin\gswin64c.exe",
            r"C:\Program Files (x86)\gs\gs*\bin\gswin32c.exe",
        ]

        import glob

        gs_exe = None
        for pattern in gs_paths:
            matches = glob.glob(pattern)
            if matches:
                gs_exe = matches[0]
                break

        if gs_exe and os.path.exists(gs_exe):
            printer = win32print.GetDefaultPrinter()

            cmd = [
                gs_exe,
                "-dPrinted",
                "-dBATCH",
                "-dNOPAUSE",
                "-dNOSAFER",
                "-q",
                "-dNumCopies=1",
                "-sDEVICE=mswinpr2",
                f"-sOutputFile=%printer%{printer}",
                pdf_path,
            ]

            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                return True

    except ImportError:
        pass
    except Exception:
        pass

    # Method 2: Try SumatraPDF (silent print, very reliable)
    sumatra_paths = [
        r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
        r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "SumatraPDF", "SumatraPDF.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "SumatraPDF", "SumatraPDF.exe"),
    ]

    # Also search in PATH
    try:
        result = subprocess.run(["where", "SumatraPDF.exe"], capture_output=True, text=True)
        if result.returncode == 0:
            sumatra_in_path = result.stdout.strip().split("\n")[0]
            if sumatra_in_path:
                sumatra_paths.insert(0, sumatra_in_path)
    except:  # noqa
        pass

    for sumatra in sumatra_paths:
        if sumatra and os.path.exists(sumatra):
            cmd = [sumatra, "-print-to-default", "-silent", pdf_path]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    return True
            except Exception:
                pass

    # Method 3: Try Adobe Reader
    adobe_paths = [
        r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe",
        r"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
        r"C:\Program Files\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
    ]

    for adobe in adobe_paths:
        if os.path.exists(adobe):
            cmd = [adobe, "/p", pdf_path]
            try:
                subprocess.Popen(cmd)
                return True
            except Exception:
                pass

    # Method 4: Try win32api.ShellExecute as last resort
    try:
        import win32api  # noqa

        win32api.ShellExecute(0, "print", pdf_path, None, ".", 0)
        return True
    except ImportError:
        pass
    except Exception:
        pass

    return False


def print_pdf(pdf_path):
    """Print a PDF file using the default printer."""

    if not os.path.exists(pdf_path):
        return False

    system = platform.system()

    try:
        if system == "Windows":
            return print_pdf_windows(pdf_path)

        elif system in ["Darwin", "Linux"]:  # macOS and Linux
            cmd = ["lp", pdf_path]
            subprocess.run(cmd, check=True)

        return True

    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False


# def main():
#     """Main function to handle PDF printing."""

#     # Get PDF file path from command line argument or user input
#     if len(sys.argv) > 1:
#         pdf_path = sys.argv[1]
#     else:
#         pdf_path = input("Enter the path to the PDF file: ").strip()

#     # Print the PDF to default printer
#     print_pdf(pdf_path)


# if __name__ == "__main__":
#     main()
