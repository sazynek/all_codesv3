mod program;
use program::program;

#[tokio::main]
async fn main() {
    program().await;
}
