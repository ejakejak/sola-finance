const fs = require('node:fs');
const { google } = require('googleapis');

const SPREADSHEET_ID = process.env.SOLA_SPREADSHEET_ID;
const DRIVE_FOLDER_ID = process.env.SOLA_DRIVE_FOLDER_ID;

function getCredentials() {
  if (process.env.GOOGLE_SERVICE_ACCOUNT_JSON) {
    try {
      return JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_JSON);
    } catch {
      throw new Error('GOOGLE_SERVICE_ACCOUNT_JSON bukan JSON yang valid.');
    }
  }

  const credentialPath = process.env.GOOGLE_APPLICATION_CREDENTIALS;
  if (credentialPath && fs.existsSync(credentialPath)) {
    return JSON.parse(fs.readFileSync(credentialPath, 'utf8'));
  }

  throw new Error('Kredensial Google belum dikonfigurasi.');
}

function getGoogleClients() {
  if (!SPREADSHEET_ID || !DRIVE_FOLDER_ID) {
    throw new Error('ID spreadsheet atau folder Drive belum dikonfigurasi.');
  }

  const auth = new google.auth.GoogleAuth({
    credentials: getCredentials(),
    scopes: [
      'https://www.googleapis.com/auth/spreadsheets',
      'https://www.googleapis.com/auth/drive',
    ],
  });

  return {
    sheets: google.sheets({ version: 'v4', auth }),
    drive: google.drive({ version: 'v3', auth }),
  };
}

module.exports = { getGoogleClients, SPREADSHEET_ID, DRIVE_FOLDER_ID };
