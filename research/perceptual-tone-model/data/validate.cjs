// Validate the new research contract without changing the pinned v1 replay schema.
const fs = require('node:fs');
const path = require('node:path');
const Ajv = require(path.resolve(__dirname, '../../../apps/mobile/node_modules/ajv'));
const schema = JSON.parse(fs.readFileSync(path.join(__dirname, 'dataset.schema.json')));
const validate = new Ajv({ allErrors: true }).compile(schema);
const rows = JSON.parse(fs.readFileSync(0, 'utf8'));
for (const row of rows) {
  if (!validate(row)) {
    console.error(JSON.stringify({ example_id: row.example_id, errors: validate.errors }));
    process.exit(1);
  }
}
