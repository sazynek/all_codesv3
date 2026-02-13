use iced::Color;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum Page {
    Home,
    Redactor,
    Settings,
    About,
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum System {
    Linux,
    Windows,
    MacOS,
    Any,
}

impl System {
    pub fn matches_current(&self) -> bool {
        match self {
            System::Linux => cfg!(target_os = "linux"),
            System::Windows => cfg!(target_os = "windows"),
            System::MacOS => cfg!(target_os = "macos"),
            System::Any => true,
        }
    }

    pub fn all() -> Vec<System> {
        vec![System::Linux, System::Windows, System::MacOS, System::Any]
    }
}

impl std::fmt::Display for System {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self)
    }
}

impl From<System> for String {
    fn from(system: System) -> Self {
        format!("{:?}", system)
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum RedactorMode {
    Create,
    Combine,
    Redact,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommandInfo {
    pub title: String,
    pub command: String,
    pub system: System,
    pub default_command: bool,
    pub need_root: bool,
}

impl CommandInfo {
    pub fn new(
        title: &str,
        command: &str,
        system: System,
        default_command: bool,
        need_root: bool,
    ) -> Self {
        Self {
            title: title.to_string(),
            command: command.to_string(),
            system,
            default_command,
            need_root,
        }
    }
}


pub struct RedactorFields {
    pub value:RedactorValue,
    pub error_text:String,
    pub color:Color,
    pub required: bool
}

pub enum  RedactorValue{
    String(String),
    Int(i32),
    Bool(bool),


}
