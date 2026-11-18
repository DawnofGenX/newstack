use tokio::sync::broadcast;

pub type Message = String;

#[derive(Clone)]
pub struct Hub {
    tx: broadcast::Sender<Message>,
}

impl Hub {
    pub fn new(capacity: usize) -> Self {
        let (tx, _) = broadcast::channel(capacity);
        Self { tx }
    }

    pub fn subscribe(&self) -> broadcast::Receiver<Message> {
        self.tx.subscribe()
    }

    pub fn broadcast(&self, message: Message) -> usize {
        self.tx.send(message).unwrap_or(0)
    }

    pub fn subscriber_count(&self) -> usize {
        self.tx.receiver_count()
    }
}
