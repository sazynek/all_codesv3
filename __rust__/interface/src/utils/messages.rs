use crate::utils::{RedactorMode, System};

#[derive(Debug, Clone)]
pub enum RedactorMessage {
    // settings for new commands
    RedactorTitle(String),     // must
    RedactorCommand(String),   // must
    RedactorSetSystem(System), // opt
    RedactorSetNeedRoot(bool), // must
    // not settings
    // change mode redactor
    RedactorModeChanged(RedactorMode),
    // create new command
    RedactorAddCommand,
    // error
    // RedactorError(String)
}
