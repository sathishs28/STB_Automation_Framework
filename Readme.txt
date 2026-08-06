### This is an Automation Framework for STB testing ###

Requirement:
    To run this automation project, you need to install the following packages and plugins

    1. redrat hub (Refer the STB_Automation_29052026.docx document)  
    2. pytest - Pytest for Unittest framework
   
*** For Fresh Setup in New PC ***
Note: If already setup has done, ignore below steps 1,2, & 3. continue on step 4 & 5

Step 1. Clone the Code and install Python V3.11 & Chrome Webdriver
    1. Clone url - https://github.com/sathishs28/OVT_ONT_OP2200H_Automation.git

    2. Install the Python V3.14.6 - https://www.python.org/downloads/ or Refer the /Setup_files/Python directory

    3. Install the .NET_Runtime .exe files (3 files there)
        Note: For more details, refer redrat official site.

    4. Install OCR (ocr.py – Optical Character Recognition):
        •	Install ocr pytessaract.
            # pip install pytesseract pillow
        •	install Tesseract OCR engine on Windows — it's a separate binary. Go to the url - https://github.com/UB-Mannheim/tesseract/wiki
        •	Download and install the .exe file.
        •	After installed, add the environment path of installed location.
        •	Then check the version
            # tesseract –version


Step 2. Set Up a Virtual Environment:
    1. Open a terminal or command prompt on the other PC.

    2. Navigate to your project directory using the cd command:
        cd path/to/your/project

    3. Create a new virtual environment:
        python -m venv .venv

    4. Activate the virtual environment:
        .\.venv\Scripts\activate.bat

Step 3. Install Project Dependencies:
    pip install -r requirements.txt


Step 4. After setup done, verify the IR blaster Unittest & Smoke testing, run following cmds

    For Unittest:
        python -m unittest tests.unit_tests.unittest_redrat_client

        python -m unittest tests.unit_tests.unittest_device_manager
    For Smoke test: (Basic test Scripts there, need to update later)
        # Smoke test for IR validate.
        python -m tests.smoke_tests.ir_device_smoke_test

        # Smoke test for IR + Capture device.
        python -m tests.smoke_tests.ir+capture_smoke_test 

    After run the smoke testing, given key signal responsed in STB.



