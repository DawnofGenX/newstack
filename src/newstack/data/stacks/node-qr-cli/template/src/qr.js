import QRCode from 'qrcode';

export async function generatePng(text, outputPath, options = {}) {
  await QRCode.toFile(outputPath, text, {
    width: options.width ?? 256,
    margin: options.margin ?? 1,
    errorCorrectionLevel: options.level ?? 'M',
  });
  return outputPath;
}

export async function renderTerminal(text) {
  return QRCode.toString(text, { type: 'terminal', small: true });
}