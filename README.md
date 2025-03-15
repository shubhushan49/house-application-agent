## Running the project
- python3 main.py
    - save configuration (inputs)
        - username
        - password
        - city
        - Intro Text for WG
        - Intro Text for Other types of apartments
    
    - run the bot

    - exit
        - click on the cancel run button
        - manually close the browser opened by selenium

## TODO
### Process Architecture
- There are two processes:
    - UI
    - Bot/Backend

Problems:
- When cancel run is pressed, the process terminates but the selenium browser does not close
- Create pipes or events to send an exit event to the bot process from the UI
    - Close the browser before terminating the process