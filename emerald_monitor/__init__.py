import psutil
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from threading import Thread

import contextlib

@contextlib.contextmanager
def resource_monitor(*arg, **kw):
    monitor = ResourceMonitor(*arg, **kw)
    monitor.start_logging()
    try:
        yield monitor
    finally:
        monitor.stop_logging()
#
# with resource_monitor() as monitor:
#   do_inversion()

# logs = monitor.get_logs()


class ResourceMonitor(Thread):

    def __init__(self, logging_interval=1):
        super().__init__()
        self.daemon = True  # Set as daemon to terminate with main program
        self.running = False
        # One list of (epoch, cpu_times, memory_info) tuples rather than three parallel lists.
        # get_logs() used to size the frame from len(self.epoch_time) and then index all three;
        # called while run() was mid-append that raised IndexError on the shorter lists.
        self.samples = []
        self.marks = []          # (name, t_start, t_end) spans, see mark()/section()
        self.kernel_process = psutil.Process()
        self.logging_interval = logging_interval

    # Kept so existing callers that read these keep working.
    @property
    def epoch_time(self):
        return [s[0] for s in self.samples]

    @property
    def cpu_times(self):
        return [s[1] for s in self.samples]

    @property
    def memory_info(self):
        return [s[2] for s in self.samples]

    def start_logging(self):
        # Check if already running to avoid conflicts
        if self.running:
            print("Monitoring already in progress.")
            return
        self.running = True
        self.start()  # Thread automatically calls run()

    def stop_logging(self, join=True, timeout=None):
        """Stop sampling.

        ``join`` waits for the sampling thread to actually exit before returning. Without it the
        thread can still be inside its ``time.sleep(logging_interval)`` and append one more
        sample after the caller believes logging has stopped.
        """
        self.running = False
        if join and self.is_alive():
            self.join(timeout if timeout is not None else self.logging_interval + 1.0)

    def run(self):
        while self.running:
            try:
                kernel_process = self.kernel_process
                # Appended as ONE tuple so a reader can never see a partially-written sample.
                self.samples.append((time.time(),
                                     kernel_process.cpu_times(),
                                     kernel_process.memory_info()))

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Handle potential issues with the kernel process
                print(f"Error monitoring process with PID {self.kernel_process.pid}. Stopping logging.")
                break
            time.sleep(self.logging_interval)  # Use the set logging interval # s

    def mark(self, name, t_start, t_end):
        """Record a named span against the same clock as the samples (``time.time()``)."""
        self.marks.append({'section': name, 'start': float(t_start), 'end': float(t_end)})

    @contextlib.contextmanager
    def section(self, name, verbose=True):
        """Label a span of the run.

        The sample timeline says how much memory and CPU were used and when; it has no idea what
        the process was doing. Wrapping work in a section records the boundaries so the timeline
        can be attributed afterwards -- per-section duration and peak memory -- and so
        ``plot_logs()`` can shade and label them.

            with monitor.section('load'):
                ...
        """
        t0 = time.time()
        if verbose:
            print(f"  -- {name} ...")
        try:
            yield self
        finally:
            t1 = time.time()
            self.mark(name, t0, t1)
            if verbose:
                print(f"  -- {name}: {t1 - t0:,.1f} s")

    def get_section_summary(self):
        """Per-section duration, peak RSS and RSS change. Empty if no sections were marked."""
        if not self.marks:
            return pd.DataFrame()
        logs = self.get_logs()
        rows = []
        for m in self.marks:
            w = logs[(logs.epoch_time >= m['start']) & (logs.epoch_time <= m['end'])]
            rows.append({
                'section': m['section'],
                'seconds': m['end'] - m['start'],
                'peak_rss_gb': w.memory_rss.max() if len(w) else np.nan,
                'delta_rss_gb': (w.memory_rss.iloc[-1] - w.memory_rss.iloc[0]) if len(w) > 1
                                else np.nan,
                'n_samples': len(w),
            })
        out = pd.DataFrame(rows)
        out['pct_time'] = 100 * out.seconds / out.seconds.sum()
        return out

    def get_logs(self):
        columns = ['epoch_time', 'elapsed_time', 'memory_rss', 'cpu_times_user', 'cpu_times_system', 'cpu_times_total']
        samples = list(self.samples)          # snapshot; run() may still be appending
        monitor_info = pd.DataFrame(np.ones([len(samples), len(columns)]), columns=columns)
        for ii in range(0, len(samples), 1):
            now_time = samples[ii][0]
            gm_time = time.gmtime(now_time)

            numdec = 3
            dec_sec = f'0{np.round(gm_time.tm_sec + (now_time - np.floor(now_time)), numdec)}0'
            dec_sec = dec_sec.split('.')[0][-2:] + '.' + dec_sec.split('.')[1][:numdec]

            monitor_info.loc[ii, 'epoch_time'] = now_time
            monitor_info.loc[ii, 'elapsed_time'] = now_time - samples[0][0]
            monitor_info.loc[ii, 'gm_year'] = gm_time.tm_year
            monitor_info.loc[ii, 'gm_month'] = gm_time.tm_mon
            monitor_info.loc[ii, 'gm_day'] = gm_time.tm_mday
            monitor_info.loc[ii, 'gm_time'] = f"{gm_time.tm_hour}:{gm_time.tm_min}:{dec_sec}"
            monitor_info.loc[ii, 'memory_rss'] = samples[ii][2].rss / (1024 ** 3)
            monitor_info.loc[ii, 'cpu_times_user'] = samples[ii][1].user
            monitor_info.loc[ii, 'cpu_times_system'] = samples[ii][1].system
            monitor_info.loc[ii, 'cpu_times_total'] = samples[ii][1].user + samples[ii][1].system

        return monitor_info

    def plot_logs(self, time_key='elapsed_time', figsize=(10, 5)):
        # time_key = 'epoch_time'
        monitor_info = self.get_logs()

        fig, axs = plt.subplots(nrows=4, ncols=1, sharex=True, figsize=figsize)
        axs[0].plot(monitor_info[time_key], monitor_info.memory_rss, label="memory_rss", c='blue')
        axs[0].set_ylabel(f"memory usage (Gb)")

        axs[1].plot(monitor_info[time_key], monitor_info.memory_rss.diff(), label="memory_change", c='blue')
        axs[1].set_ylabel(f"memory usage change (Gb)")

        axs[2].plot(monitor_info[time_key], monitor_info.cpu_times_total, label='total', c="red")
        axs[2].plot(monitor_info[time_key], monitor_info.cpu_times_system, label='system', c="green")
        axs[2].plot(monitor_info[time_key], monitor_info.cpu_times_user, label='user', c="orange")
        axs[2].legend()
        axs[2].set_ylabel(f"cpu times")

        axs[3].plot(monitor_info[time_key], monitor_info.cpu_times_total.diff(), label="total_change", c='red')
        axs[3].plot(monitor_info[time_key], monitor_info.cpu_times_system.diff(), label="system_change", c='green')
        axs[3].plot(monitor_info[time_key], monitor_info.cpu_times_user.diff(), label="user_change", c='orange')
        axs[3].legend()
        axs[3].set_ylabel(f"cpu times change")

        axs[3].set_xlabel(f"{time_key} (s)")

        plt.tight_layout()
        plt.show()
        
