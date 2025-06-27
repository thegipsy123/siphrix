import fs from 'fs/promises';
import path from 'path';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  const { user } = req.query; // like "abcd123.enc"
  const data = req.body;

  const dir = path.join(process.cwd(), 'public', 'userdata');
  await fs.mkdir(dir, { recursive: true }); // make sure folder exists

  const filePath = path.join(dir, `${user}.enc.json`);

  await fs.writeFile(filePath, JSON.stringify(data, null, 2), 'utf-8');

  res.status(200).json({ message: 'Vault saved successfully' });
}
