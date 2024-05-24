import PySimpleGUI as sg
import subprocess
import os

def main():
    sg.theme('BluePurple')

    # Define the layout of the window
    layout = [
        [sg.Text('Scheduler Type:'), sg.Combo(['fcfs', 'sjf', 'rr'], default_value='fcfs', key='scheduler_type')],
        [sg.Text('Input File:'), sg.Combo(os.listdir('pa1-testfiles'), key='input_file')],
        [sg.Button('Run'), sg.Button('Exit')],
        [sg.Multiline(key='output', size=(80, 20), disabled=True)]
    ]

    # Create the window
    window = sg.Window('Scheduler Simulation', layout)

    # Event Loop
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        elif event == 'Run':
            scheduler_type = values['scheduler_type']
            input_file = values['input_file']
            if scheduler_type and input_file:
                # Construct the path to the input file
                filepath = os.path.join('pa1-testfiles', input_file)
                # Run the scheduling script and capture output
                try:
                    output = subprocess.check_output(['python3', 'scheduler-gpt.py', filepath], text=True)
                except subprocess.CalledProcessError as e:
                    output = f"An error occurred: {str(e)}"
                window['output'].update(output)
            else:
                sg.popup('Error', 'Please select a scheduler type and an input file!')

    window.close()

if __name__ == '__main__':
    main()
