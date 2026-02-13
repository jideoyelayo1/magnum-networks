# Cross Platform Visualisation System

## About

In this small project I collected data from both kalashi and polymarket to compare the predictions.
Unformately due to time difficulties I was unable to make an automatic matching system which would allow things such as arbitrage finding. So I current I chose to look at the current 2026 MVP winner predictions.

What this project does is continously grab data from both and compare. It takes a moving average and does a monte carlo on the end to see the number of possibles paths of the prediction.

## To run

```bash
python3 -m venv venv

venv/bin/activate
OR
source venv/bin/activate
```

To collect data
```bash
python3 data_stream/main.py 
```

To run graphs
```bash
python3 market_analytics/analytics.py
```
