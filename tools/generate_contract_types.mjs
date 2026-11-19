import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { compile } from 'json-schema-to-typescript';

const root = new URL('../', import.meta.url);
const schemaPath = new URL('schemas/artifact.schema.json', root);
const typePath = new URL('packages/contracts/src/generated/artifact.ts', root);
const schema = JSON.parse(await readFile(schemaPath, 'utf8'));
const generated = await compile(schema, 'Artifact', { bannerComment: '' });

if (process.argv.includes('--check')) {
  let current;
  try {
    current = await readFile(typePath, 'utf8');
  } catch {
    current = '';
  }
  if (current !== generated) {
    console.error(
      'packages/contracts/src/generated/artifact.ts is out of date; run make generate-contracts',
    );
    process.exitCode = 1;
  } else {
    console.log('JSON Schema and TypeScript types agree.');
  }
} else {
  await mkdir(new URL('packages/contracts/src/generated/', root), {
    recursive: true,
  });
  await writeFile(typePath, generated, 'utf8');
  console.log('Wrote packages/contracts/src/generated/artifact.ts');
}
