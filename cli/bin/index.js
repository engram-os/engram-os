#!/usr/bin/env node

import { program } from 'commander';
import inquirer from 'inquirer';
import { execa } from 'execa';
import chalk from 'chalk';
import ora from 'ora';
import fs from 'fs';
import path from 'path';
import degit from 'degit';


const REPO_URL = 'your-github-username/engram-os'; 
const TARGET_DIR = process.cwd();

program
  .version('1.0.0')
  .description('Engram OS - Local First AI Operating System CLI')
  .action(async () => {
    console.log(chalk.bold.blue('\n🧠 Welcome to Engram OS Installer\n'));
    await runInstaller();
  });

async function runInstaller() {
  const spinner = ora('Checking system requirements...').start();
  try {
    await execa('docker', ['--version']);
    await execa('docker', ['compose', 'version']);
    spinner.succeed('Docker is installed and ready.');
  } catch (error) {
    spinner.fail('Docker is missing or not running.');
    console.log(chalk.red('Error: Please install Docker Desktop and ensure it is running before proceeding.'));
    process.exit(1);
  }

  const { installPath } = await inquirer.prompt([
    {
      type: 'input',
      name: 'installPath',
      message: 'Where should we install Engram?',
      default: './engram-local',
    },
  ]);

  const fullPath = path.resolve(TARGET_DIR, installPath);
  
  if (fs.existsSync(fullPath)) {
    const { overwrite } = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'overwrite',
        message: `Directory ${installPath} already exists. Overwrite?`,
        default: false,
      }
    ]);
    if (!overwrite) process.exit(0);
  }

  const downloadSpinner = ora('Downloading Engram core files...').start();
  try {
    const emitter = degit(REPO_URL, { cache: false, force: true });
    await emitter.clone(fullPath);
    downloadSpinner.succeed(`Downloaded Core to ${chalk.green(fullPath)}`);
  } catch (err) {
    downloadSpinner.fail('Failed to download repository.');
    console.error(err);
    process.exit(1);
  }

  console.log(chalk.yellow('\n Configuration Setup'));
  
  const answers = await inquirer.prompt([
    {
      type: 'input',
      name: 'OLLAMA_BASE_URL',
      message: 'Enter your local Ollama URL:',
      default: 'http://host.docker.internal:11434',
    },
    {
      type: 'list',
      name: 'LLM_MODEL',
      message: 'Which Llama 3 model are you running?',
      choices: ['llama3', 'llama3:8b', 'llama3.1'],
      default: 'llama3',
    },
  ]);

  const envContent = Object.entries(answers)
    .map(([key, value]) => `${key}=${value}`)
    .join('\n');
  
  const finalEnv = `${envContent}\n\n# System Config\nQDRANT_HOST=qdrant\nREDIS_HOST=redis\n`;
  
  fs.writeFileSync(path.join(fullPath, '.env'), finalEnv);
  console.log(chalk.green('.env file created successfully.'));

  // 4. Instructions for Google Auth
  console.log(chalk.cyan('\n IMPORTANT: Google Credentials'));
  console.log(`Please place your ${chalk.bold('credentials.json')} and ${chalk.bold('token.json')} inside:`);
  console.log(chalk.white(`${fullPath}/credentials/`));
  
  const { ready } = await inquirer.prompt([{
    type: 'confirm',
    name: 'ready',
    message: 'Ready to launch the Operating System?',
    default: true
  }]);

  if (ready) {
    console.log(chalk.blue('\n Launching Engram via Docker Compose...'));
    console.log(chalk.dim('This might take a while on the first run (pulling images).'));
    
    const subprocess = execa('docker', ['compose', 'up', '--build', '-d'], {
      cwd: fullPath,
      stdio: 'inherit'
    });

    try {
      await subprocess;
      console.log(chalk.bold.green('\n Engram OS is ONLINE!'));
      console.log(`Dashboard: ${chalk.underline('http://localhost:8501')}`);
      console.log(`API Docs:  ${chalk.underline('http://localhost:8000/docs')}`);
    } catch (e) {
      console.error(chalk.red('Failed to start Docker containers. Check logs above.'));
    }
  }
}

program.parse(process.argv);