import sharp from 'sharp';
import { readFileSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const svgPath = join(__dirname, '../public/icons/icon.svg');
const outputDir = join(__dirname, '../public/icons');

// Ensure output directory exists
mkdirSync(outputDir, { recursive: true });

// Read the SVG file
const svgBuffer = readFileSync(svgPath);

// Generate PNG icons in different sizes
const sizes = [16, 32, 48, 128];

async function generateIcons() {
  for (const size of sizes) {
    try {
      await sharp(svgBuffer)
        .resize(size, size)
        .png()
        .toFile(join(outputDir, `icon-${size}.png`));
      
      console.log(`Generated icon-${size}.png`);
    } catch (error) {
      console.error(`Error generating icon-${size}.png:`, error);
    }
  }
}

generateIcons().then(() => {
  console.log('All icons generated successfully!');
}).catch(error => {
  console.error('Error generating icons:', error);
});