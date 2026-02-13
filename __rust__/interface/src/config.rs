use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

use crate::CommandInfo;
use crate::System;

const COMMANDS_CONFIG_PATH: &str = "settings/config.yaml";
const SETTINGS_CONFIG_PATH: &str = "settings/settings.yaml";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub commands: Vec<CommandInfo>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppSettings {
    pub show_linux: bool,
    pub show_windows: bool,
    pub show_macos: bool,
    pub show_another: bool,
    pub show_all: bool,
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            show_linux: true,
            show_windows: true,
            show_macos: true,
            show_another: true,
            show_all: true,
        }
    }
}

impl Default for Config {
    fn default() -> Self {
        Self {
            commands: get_default_commands(),
        }
    }
}

pub fn load_config() -> Config {
    if !Path::new(COMMANDS_CONFIG_PATH).exists() {
        let default_config = Config::default();
        save_config(&default_config).expect("Failed to save default config");
        return default_config;
    }

    let content = fs::read_to_string(COMMANDS_CONFIG_PATH).expect("Failed to read config file");
    serde_yaml::from_str(&content).expect("Failed to parse config file")
}

pub fn save_config(config: &Config) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(parent) = Path::new(COMMANDS_CONFIG_PATH).parent() {
        fs::create_dir_all(parent)?;
    }

    let yaml = serde_yaml::to_string(config)?;
    fs::write(COMMANDS_CONFIG_PATH, yaml)?;
    Ok(())
}

pub fn load_settings() -> AppSettings {
    if !Path::new(SETTINGS_CONFIG_PATH).exists() {
        let default_settings = AppSettings::default();
        save_settings(&default_settings).expect("Failed to save default settings");
        return default_settings;
    }

    let content = fs::read_to_string(SETTINGS_CONFIG_PATH).expect("Failed to read settings file");
    serde_yaml::from_str(&content).expect("Failed to parse settings file")
}

pub fn save_settings(settings: &AppSettings) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(parent) = Path::new(SETTINGS_CONFIG_PATH).parent() {
        fs::create_dir_all(parent)?;
    }

    let yaml = serde_yaml::to_string(settings)?;
    fs::write(SETTINGS_CONFIG_PATH, yaml)?;
    Ok(())
}

fn get_default_commands() -> Vec<CommandInfo> {
    vec![
        CommandInfo::new(
            "Create test file",
            "touch testfile.txt",
            System::Linux,
            true,
            false,
        ),
        CommandInfo::new("List directory", "ls -la", System::Linux, true, false),
        CommandInfo::new("Show current path", "pwd", System::Linux, true, false),
        CommandInfo::new(
            "Create directory",
            "mkdir new_folder",
            System::Linux,
            true,
            false,
        ),
        CommandInfo::new("System info", "uname -a", System::Linux, true, false),
        CommandInfo::new("Update packages", "apt update", System::Linux, true, false),
        CommandInfo::new(
            "Install package",
            "apt install package-name",
            System::Linux,
            true,
            false,
        ),
        CommandInfo::new("Check disk space", "df -h", System::Linux, true, false),
        CommandInfo::new("Process list", "ps aux", System::Linux, true, false),
        CommandInfo::new("Network info", "ifconfig", System::Linux, true, false),
        CommandInfo::new("Windows dir", "dir", System::Windows, true, false),
        CommandInfo::new(
            "Windows system info",
            "systeminfo",
            System::Windows,
            true,
            false,
        ),
        CommandInfo::new("IP configuration", "ipconfig", System::Windows, true, false),
        CommandInfo::new("Network stats", "netstat", System::Windows, true, false),
        CommandInfo::new("Task list", "tasklist", System::Windows, true, false),
        CommandInfo::new("Service list", "sc query", System::Windows, true, false),
        CommandInfo::new("MacOS list", "ls -la", System::MacOS, true, false),
        CommandInfo::new(
            "MacOS system info",
            "system_profiler SPSoftwareDataType",
            System::MacOS,
            true,
            false,
        ),
        CommandInfo::new("Brew update", "brew update", System::MacOS, true, false),
        CommandInfo::new("Git status", "git status", System::Any, true, false),
        CommandInfo::new("Git log", "git log --oneline", System::Any, true, false),
        CommandInfo::new("Docker ps", "docker ps", System::Any, true, false),
        CommandInfo::new("Node version", "node --version", System::Any, true, false),
        CommandInfo::new(
            "Update System",
            "apt update && apt upgrade -y",
            System::Linux,
            true,
            false,
        ),
        CommandInfo::new(
            "Clean Package Cache",
            "apt clean",
            System::Linux,
            true,
            false,
        ),
        CommandInfo::new(
            "View System Logs",
            "journalctl -f",
            System::Linux,
            true,
            false,
        ),
        CommandInfo::new(
            "List Services",
            "systemctl list-units --type=service",
            System::Linux,
            true,
            false,
        ),
        CommandInfo::new(
            "Restart Network",
            "systemctl restart networking",
            System::Linux,
            true,
            false,
        ),
        CommandInfo::new("Check Disk Space", "df -h", System::Linux, true, false),
        CommandInfo::new(
            "Python version",
            "python --version",
            System::Any,
            true,
            false,
        ),
        CommandInfo::new("Pip list", "pip list", System::Any, true, false),
        CommandInfo::new("Rust version", "rustc --version", System::Any, true, false),
        CommandInfo::new("Cargo build", "cargo build", System::Any, true, false),
        CommandInfo::new("NPM version", "npm --version", System::Any, true, false),
        CommandInfo::new("Date and time", "date", System::Any, true, false),
        CommandInfo::new("Calendar", "cal", System::Linux, true, false),
        CommandInfo::new("Memory usage", "free -h", System::Linux, true, false),
        CommandInfo::new("CPU info", "lscpu", System::Linux, true, false),
        CommandInfo::new("Environment variables", "env", System::Any, true, false),
        CommandInfo::new("Current user", "whoami", System::Any, true, false),
        CommandInfo::new("System uptime", "uptime", System::Linux, true, false),
    ]
}
