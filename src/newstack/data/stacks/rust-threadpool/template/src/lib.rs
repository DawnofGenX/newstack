use std::sync::mpsc::{self, Receiver, Sender};
use std::sync::{Arc, Mutex};
use std::thread::{self, JoinHandle};

type Job = Box<dyn FnOnce() + Send + 'static>;

struct Worker {
    handle: Option<JoinHandle<()>>,
}

pub struct ThreadPool {
    workers: Vec<Worker>,
    sender: Option<Sender<Job>>,
    size: usize,
    shutdown: bool,
}

impl ThreadPool {
    pub fn new(size: usize) -> Self {
        assert!(size > 0, "pool size must be > 0");
        let (sender, receiver) = mpsc::channel::<Job>();
        let receiver = Arc::new(Mutex::new(receiver));
        let mut workers = Vec::with_capacity(size);
        for _ in 0..size {
            let receiver = Arc::clone(&receiver);
            let handle = thread::spawn(move || {
                loop {
                    let job = {
                        let lock = receiver.lock().unwrap();
                        lock.recv()
                    };
                    match job {
                        Ok(job) => job(),
                        Err(_) => break,
                    }
                }
            });
            workers.push(Worker {
                handle: Some(handle),
            });
        }
        ThreadPool {
            workers,
            sender: Some(sender),
            size,
            shutdown: false,
        }
    }

    pub fn size(&self) -> usize {
        self.size
    }

    pub fn submit<F, T>(&mut self, f: F) -> Result<Receiver<T>, &'static str>
    where
        F: FnOnce() -> T + Send + 'static,
        T: Send + 'static,
    {
        if self.shutdown {
            return Err("pool is shut down");
        }
        let sender = self.sender.as_ref().ok_or("pool is shut down")?;
        let (tx, rx) = mpsc::channel();
        let job = Box::new(move || {
            let _ = tx.send(f());
        });
        sender.send(job).map_err(|_| "pool is shut down")?;
        Ok(rx)
    }

    pub fn shutdown(&mut self) {
        if self.shutdown {
            return;
        }
        self.shutdown = true;
        self.sender = None;
        for worker in &mut self.workers {
            if let Some(handle) = worker.handle.take() {
                let _ = handle.join();
            }
        }
    }
}

impl Drop for ThreadPool {
    fn drop(&mut self) {
        self.shutdown();
    }
}
