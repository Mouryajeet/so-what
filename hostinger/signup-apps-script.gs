/**
 * So What? Monday signups → this Google Sheet.
 * Setup (Mourya, in your own Google account):
 *  1. Create a Google Sheet named "So What? signups". Row 1: Date | Name | Contact | Consent | Page
 *  2. Extensions → Apps Script. Paste this file. Save.
 *  3. Deploy → New deployment → type "Web app". Execute as: Me. Who has access: Anyone. Deploy, allow access.
 *  4. Copy the Web app URL (ends in /exec) and send it to Claude. It goes into site.json → signup_endpoint.
 */
function doPost(e) {
  var p = (e && e.parameter) || {};
  var name = String(p.name || '').slice(0, 120), contact = String(p.contact || '').slice(0, 160);
  if (!name || !contact || p.consent !== 'yes') return ContentService.createTextOutput('missing');
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  sheet.appendRow([new Date(), name, contact, 'yes', String(p.page || '').slice(0, 80)]);
  return ContentService.createTextOutput('ok');
}
