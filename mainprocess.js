import path from 'path';
import { fileURLToPath } from 'url';
import chalk from "chalk";
import readline from "readline";
import { spawn } from 'node:child_process';
import { dirname } from 'path';
import fetch from 'node-fetch';
import https from 'https';

const currentversion = '1.6.0'
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename)
const prompt = (query) => new Promise((resolve) => rl.question(query, resolve));
const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});





async function versioncheck() {
    let data = ''
    https.get('https://squawksquad.net/forgedytversion.txt', (response) => {

        response.on('data', (chunk) => {
            data += chunk;
        })

        response.on('end', () => {
            console.log(chalk.italic(`data: ${data} (${typeof data})\ncurrentversion: ${currentversion} (${typeof currentversion})\nidentical? ${currentversion === data}`))
            if (!(data === currentversion)) {
                return console.log([chalk.gray.italic("ForgeYT Has an update! Please Install the Latest Version from "), chalk.blueBright.underline.italic(`https://squawksquad.net/forgeyt.zip`), chalk.gray.italic((' (ctrl + click)'))].join(''))
            }
            else { console.log("Version check: Up to date") }
            banner()
        })
        response.on('error', (error) => {
            console.log(chalk.black.bgHex('#850000')(error));
        })
    })
};




async function banner(banner) {
    console.clear
    console.log('\n')
    console.log(chalk.red('     ███████╗ ██████╗ ██████╗  ██████╗ ███████╗██╗   ██╗████████╗'))
    console.log(chalk.red('     ██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝╚██╗ ██╔╝╚══██╔══╝'))
    console.log(chalk.red('     █████╗  ██║   ██║██████╔╝██║  ███╗█████╗   ╚████╔╝    ██║   '))
    console.log(chalk.red('     ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝    ╚██╔╝     ██║   '))
    console.log(chalk.red('     ██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗   ██║      ██║   '))
    console.log(chalk.red('     ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝      ╚═╝   '))
    console.log(chalk.red('     ███████████████████████████████████████████████████████████╗'))
    console.log(chalk.red('     ╚══════════════════════════════════════════════════════════╝'))
    console.log('\n\n')
    console.log(chalk.gray.italic("If you are experiencing issues, type \'issue\' in the YT Url section."))
    doPrompts()
}

const folder = path.join(__dirname, '..\\')
const filetypes = {
    "ogg": {
        "filetype": "vorbis",
        "fileext": "ogg",
        "audio": true
    },
    "vorbis": {
        "filetype": "vorbis",
        "fileext": "ogg",
        "audio": true
    },
    "default": {
        "filetype": "mp3",
        "fileext": "mp3",
        "audio": true
    },
    "mp3": {
        "filetype": "mp3",
        "fileext": "mp3",
        "audio": true
    },
    "avi": {
        "filetype": "avi",
        "fileext": "avi",
        "audio": false
    },
    "flv": {
        "filetype": "flv",
        "fileext": "flv",
        "audio": false
    },
    "mkv": {
        "filetype": "mkv",
        "fileext": "mkv",
        "audio": false
    },
    "mov": {
        "filetype": "mov",
        "fileext": "mov",
        "audio": false
    },
    "mp4": {
        "filetype": "mp4",
        "fileext": "mp4",
        "audio": false
    },
    "webm": {
        "filetype": "webm",
        "fileext": "webm",
        "audio": true
    },
    "aac": {
        "filetype": "aac",
        "fileext": "aac",
        "audio": true
    },
    "aiff": {
        "filetype": "aiff",
        "fileext": "aiff",
        "audio": true
    },
    "alac": {
        "filetype": "aiac",
        "fileext": "aiac",
        "audio": true
    },
    "flac": {
        "filetype": "flac",
        "fileext": "flac",
        "audio": true
    },
    "m4a": {
        "filetype": "m4a",
        "fileext": "m4a",
        "audio": true
    },
    "mka": {
        "filetype": "mka",
        "fileext": "mka",
        "audio": true
    },
    "opus": {
        "filetype": "opus",
        "fileext": "opus",
        "audio": true
    },
    "wav": {
        "filetype": "wav",
        "fileext": "wav",
        "audio": true
    },
    "": {
        "filetype": "mp3",
        "fileext": "mp3",
        "audio": true
    }
}


const supportedfiletypes = Array.from(Object.keys(filetypes))

async function download(yturl, ftype) {
    let filetype = (filetypes[ftype] ?? "default").filetype
    let fileext = (filetypes[ftype] ?? "default").fileext
    let audio = (filetypes[ftype] ?? "default").audio
    console.log('Youtube URL: ' + yturl)
    if (audio == true) {
        const command = `${__dirname}\\yt-dlp.exe`;
        const args = [
            '-x',
            '-f',
            '140',
            '--audio-format',
            filetype,
            '--ignore-config',
            '-o',
            `${folder}Downloads\\%(artist)s - %(title)s.${fileext}`,
            yturl
        ];
        const child = spawn(command, args);

        child.stdout.on('data', (data) => {
            console.log(`\r${data}`);
        });

        child.stderr.on('data', (data) => {
            console.error(chalk.black.bgHex('#850000')(`stderr: ${data}`));
        });

        child.on('close', (code) => {
            console.log(chalk.red.underline(`ForgeYT made by ForgedCore8, 2023, SquawkSquad`))
            setTimeout((function () {
                0
                return process.exit(1);
            }), 0);
        });
    } else if (audio == false) {
        const command = `${__dirname}\\yt-dlp.exe`;
        const args = [
            `--format-sort=ext:${fileext}`,
            '--ignore-config',
            '-o',
            `${folder}Downloads\\%(artist)s - %(title)s.${fileext}`,
            yturl
        ];
        const child = spawn(command, args);

        child.stdout.on('data', (data) => {
            console.log(`\r${data}`);
        });

        child.stderr.on('data', (data) => {
            console.error(chalk.black.bgHex('#850000')(`stderr: ${data}`));
        });

        child.on('close', (code) => {
            console.log(chalk.red.underline(`ForgeYT made by ForgedCore8, 2023, SquawkSquad`))
            setTimeout((function () {
                return process.exit(1);
            }), 0);
        });
    }



};

async function restartprompts(please) {
    doPrompts()
};

async function doPrompts(prompts) {
    const yturl = await prompt(chalk.green("Enter Youtube Link: "));
    if (yturl === 'issue') {
        const problem = await prompt(chalk.bold("What is the issue? "));
        var params = {
            username: "FORGEYT",
            content: " ",
            embeds: [
                {
                    "title": "New Report!",
                    "color": 15258703,
                    "description": problem,
                    "timestamp": `${new Date().toISOString()}`
                }
            ]
        }
        fetch('https://discord.com/api/webhooks/1077694039568162827/xBQTPoMcpV1I8DzRe2B9b5DKT-ChdW-1FO3zkuSH1HVQ5-AscZy38vZhhqfNG6JQNE6x', {
            method: "POST",
            headers: {
                'Content-type': 'application/json'
            },
            body: JSON.stringify(params)
        })
        console.log('Your Issue report: "' + problem + '" has been posted!')
        return await doPrompts()
    }
    else {
        const filetype = await prompt(chalk.cyan("What File Type? (Leave Blank For MP3): "));

        if (yturl === '') {
            console.log(chalk.bgHex('#850000').black('Youtube URL is Required.'))
            restartprompts()
            return;
        } else if (!(supportedfiletypes.includes(filetype))) {
            console.log(chalk.bgHex('#850000').black('File Type Not Supported. Supported File Types are: ' + supportedfiletypes.join(", ")))
            restartprompts()
            return;
        }
        return await download(yturl, filetype)
    }
};
versioncheck()
