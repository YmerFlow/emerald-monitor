This is a simple monitoring class built around psutil. The idea is that this will monitor cpu and ram usage between starting and stopping the monitoring. 

1) To use simply import the package: ```from emerald_monitor import ResourceMonitor```

2) Then you can initialize the monitor: ```monitor = ResourceMonitor()```

3) Start the logger: ```monitor.start_logging()```

4) Run any function or process

5) Stop the logger: ```monitor.stop_logging()```

You can view a plot of the logs using:
  - ```monitor.plot_logs()```
  - ![image](https://github.com/user-attachments/assets/5b97d775-5d2e-4e13-91a9-86f9b593e2e4)

and, you can view the logs as a pandas dataframe:
  - ```monitor_info = monitor.get_logs()```.
  - ![image](https://github.com/user-attachments/assets/294ca81f-4cbf-4e37-a980-f0031438eac3)

And, of course you can export the logs using pandas export options. For example:
  - ```monitor_info.to_csv(<output file path>, index=False)```

See the example usage notebook for a more detailed out line of the usage

## Running the tests

Install the test extra and run pytest from the repository root:

```
pip install -e .[test]
pytest
```

The tests use a short sampling interval and run headlessly (matplotlib is pinned to the Agg
backend), so the whole suite takes a few seconds and never opens a plot window.
