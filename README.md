# CoveredCallCalculator

Idea: programatically generate possible yields from buying a stock just to write covered calls on. Every morning push a new set of csv's to a google drive directory with an updatable ticker list, as well as send contracts with the highest yields to my phone via sms.

Api's utilized:
- twilio
- td ameritrade

Current progress:
- windows task scheduled to run this main.py every morning with a ticker list in the Google Drive directory, pushes csv's up to the same directory
    - text message sent through twilio api as well


Future:
- some aws instance running this -- what if my personal desktop is off?
- have this service live throughout the day so I can query individual tickers to have these calculations done for me on the fly.
- config for some hardcoded variables like phone numbers, file paths
- don't like the way pretty print is accessing variables from contract directly, make pretty print prettier


Quick text example:

<img src = images/text.png width=400>
