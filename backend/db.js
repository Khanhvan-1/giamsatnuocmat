const { Pool } = require('pg');

const pool = new Pool({
  user: 'postgres',          // tên user của bạn
  host: 'localhost',
  database: 'webgis_nuoc',   // tên database của bạn
  password: '123456',      // mật khẩu
  port: 5432,
});

module.exports = pool;