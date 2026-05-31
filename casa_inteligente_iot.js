function doPost(e) {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var dados = JSON.parse(e.postData.contents);
  sheet.appendRow([
    dados.datetime,
    dados.temperatura,
    dados.umidade,
    dados.ldr,
    dados.gas,
    dados.movimento,
    dados.relay1,
    dados.relay2,
    dados.relay3,
    dados.relay4
  ]);
  return ContentService.createTextOutput("OK");
}