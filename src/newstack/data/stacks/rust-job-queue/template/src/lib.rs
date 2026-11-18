#![allow(clippy::all)]

use std::sync::mpsc::{self, Receiver, Sender};
use std::sync::{Arc, Mutex};
use std::thread::{self, JoinHandle};

pub type JobFn = Arc<dyn Fn() -> Result<(), String> + Send + Sync>;

#[derive(Debug, Clone)]
pub struct JobResult {
    pub ok: bool,
    pub attempts: usize,
    pub error: Option<String>,
}

pub struct JobQueue {
    tx: Option<Sender<JobFn>>,
    results_rx: Receiver<JobResult>,
    workers: Vec<JoinHandle<()>>,
    max_attempts: usize,
    shutdown: bool,
}

impl JobQueue {
    pub fn new(workers: usize, max_attempts: usize) -> Self {
        assert!(workers > 0, "workers must be > 0");
        assert!(max_attempts > 0, "max_attempts must be > 0");
        let (tx, rx) = mpsc::channel::<JobFn>();
        let (res_tx, res_rx) = mpsc::channel::<JobResult>();
        let rx = Arc::new(Mutex::new(rx));
        let mut handles = Vec::with_capacity(workers);
        for _ in 0..workers {
            let rx = Arc::clone(&rx);
            let res_tx = res_tx.clone();
            let ma = max_attempts;
            let h = thread::spawn(move || {
                loop {
                    let job = {
                        let lock = rx.lock().unwrap();
                        lock.recv()
                    };
                    match job {
                        Ok(job) => {
                            let mut attempts = 0;
                            let mut last_err = None;
                            for _ in 0..ma {
                                attempts += 1;
                                match job() {
                                    Ok(()) => {
                                        last_err = None;
                                        break;
                                    }
                                    Err(e) => {
                                        last_err = Some(e);
                                    }
                                }
                            }
                            let ok = last_err.is_none();
                            let _ = res_tx.send(JobResult {
                                ok,
                                attempts,
                                error: last_err,
                            });
                        }
                        Err(_) => break,
                    }
                }
            });
            handles.push(h);
        }
        JobQueue {
            tx: Some(tx),
            results_rx: res_rx,
            workers: handles,
            max_attempts,
            shutdown: false,
        }
    }

    pub fn max_attempts(&self) -> usize {
        self.max_attempts
    }

    pub fn submit<F>(&self, f: F)
    where
        F: Fn() -> Result<(), String> + Send + Sync + 'static,
    {
        if let Some(tx) = &self.tx {
            let _ = tx.send(Arc::new(f));
        }
    }

    pub fn try_recv_result(&self) -> Option<JobResult> {
        self.results_rx.try_recv().ok()
    }

    pub fn recv_result(&self) -> Option<JobResult> {
        self.results_rx.recv().ok()
    }

    pub fn recv_result_timeout(&self, d: std::time::Duration) -> Option<JobResult> {
        self.results_rx.recv_timeout(d).ok()
    }

    pub fn shutdown(&mut self) {
        if self.shutdown {
            return;
        }
        self.shutdown = true;
        self.tx = None;
        for h in self.workers.drain(..) {
            let _ = h.join();
        }
    }

    pub fn is_shutdown(&self) -> bool {
        self.shutdown
    }
}

impl Drop for JobQueue {
    fn drop(&mut self) {
        self.shutdown();
    }
}
