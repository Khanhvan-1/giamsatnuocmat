const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const pool = require('./db');

const app = express();
const port = 3000;

app.use(cors());
app.use(bodyParser.json({ limit: '20mb' }));
app.use(bodyParser.urlencoded({ limit: '20mb', extended: true }));

/* =========================================================
   1) CẬP NHẬT DỮ LIỆU ĐIỂM QUAN TRẮC
========================================================= */
app.post('/api/points/update', async (req, res) => {
  const points = req.body.points;

  if (!points || !Array.isArray(points)) {
    return res.status(400).json({ error: 'Invalid data' });
  }

  try {
    await pool.query('BEGIN');

    for (const p of points) {
      const { ma_diem, ph, do: doVal, bod5, cod, nh4, coliform, lat, lng } = p;
      const geom = `POINT(${lng} ${lat})`;

      const query = `
        UPDATE diem_quan_trac_clean
        SET ph = $1,
            "do" = $2,
            bod5 = $3,
            cod = $4,
            nh4 = $5,
            caliform = $6,
            geom = ST_GeomFromText($7, 4326)
        WHERE ma_diem = $8
      `;

      const values = [ph, doVal, bod5, cod, nh4, coliform, geom, ma_diem];
      await pool.query(query, values);
    }

    await pool.query('COMMIT');
    res.json({ status: 'success', count: points.length });

  } catch (err) {
    await pool.query('ROLLBACK');
    console.error('❌ Lỗi update points:', err);
    res.status(500).json({ error: err.message });
  }
});

/* =========================================================
   2) LẤY DỮ LIỆU ĐIỂM QUAN TRẮC
========================================================= */
app.get('/api/points', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT ma_diem, ph, "do", bod5, cod, nh4,
             caliform as coliform,
             ST_AsGeoJSON(geom) as geometry
      FROM diem_quan_trac_clean
    `);

    const features = result.rows.map(row => ({
      ma_diem: row.ma_diem,
      ph: row.ph,
      do: row.do,
      bod5: row.bod5,
      cod: row.cod,
      nh4: row.nh4,
      coliform: row.coliform,
      geometry: JSON.parse(row.geometry)
    }));

    res.json(features);

  } catch (err) {
    console.error('❌ Lỗi lấy points:', err);
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/points/', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT ma_diem, ph, "do", bod5, cod, nh4,
             caliform as coliform,
             ST_AsGeoJSON(geom) as geometry
      FROM diem_quan_trac_clean
    `);

    const features = result.rows.map(row => ({
      ma_diem: row.ma_diem,
      ph: row.ph,
      do: row.do,
      bod5: row.bod5,
      cod: row.cod,
      nh4: row.nh4,
      coliform: row.coliform,
      geometry: JSON.parse(row.geometry)
    }));

    res.json(features);

  } catch (err) {
    console.error('❌ Lỗi lấy points:', err);
    res.status(500).json({ error: err.message });
  }
});

/* =========================================================
   3) LƯU CẢNH BÁO Ô NHIỄM
========================================================= */
app.post('/api/reports', async (req, res) => {
  const warnings = req.body.warnings;

  console.log("📥 Nhận warnings từ frontend:", JSON.stringify(warnings, null, 2));

  if (!warnings || !Array.isArray(warnings)) {
    return res.status(400).json({ error: 'Dữ liệu không hợp lệ' });
  }

  try {
    for (let w of warnings) {
      const segmentName =
        w.segment_name ||
        w.segment_id ||
        (w.location ? `(${w.location.lat}, ${w.location.lng})` : 'Không tên');

      const ph = w.values?.ph ?? null;
      const doVal = w.values?.do ?? null;
      const bod5 = w.values?.bod5 ?? null;
      const cod = w.values?.cod ?? null;
      const nh4 = w.values?.nh4 ?? null;
      const coliform = w.values?.coliform ?? null;

      let pollutedCount = 0;
      if (ph !== null && (ph < 6 || ph > 8.5)) pollutedCount++;
      if (doVal !== null && doVal < 4) pollutedCount++;
      if (bod5 !== null && bod5 > 12) pollutedCount++;
      if (cod !== null && cod > 30) pollutedCount++;
      if (nh4 !== null && nh4 > 0.5) pollutedCount++;
      if (coliform !== null && coliform > 5000) pollutedCount++;

      await pool.query(
        `INSERT INTO warnings (segment_name, ph, do_val, bod5, cod, nh4, coliform, polluted_count)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
        [segmentName, ph, doVal, bod5, cod, nh4, coliform, pollutedCount]
      );
    }

    res.json({ success: true, count: warnings.length });

  } catch (err) {
    console.error('❌ Lỗi lưu cảnh báo:', err);
    res.status(500).json({ error: 'Lỗi server', detail: err.message });
  }
});

/* =========================================================
   4) ROUTE PHỤ CHO FRONTEND CŨ
========================================================= */
app.post('/api/warnings/save', async (req, res) => {
  const warnings = req.body.warnings;

  console.log("📥 Nhận warnings từ frontend (route cũ):", JSON.stringify(warnings, null, 2));

  if (!warnings || !Array.isArray(warnings)) {
    return res.status(400).json({ error: 'Dữ liệu không hợp lệ' });
  }

  try {
    for (let w of warnings) {
      const segmentName =
        w.segment_name ||
        w.segment_id ||
        (w.location ? `(${w.location.lat}, ${w.location.lng})` : 'Không tên');

      const ph = w.values?.ph ?? null;
      const doVal = w.values?.do ?? null;
      const bod5 = w.values?.bod5 ?? null;
      const cod = w.values?.cod ?? null;
      const nh4 = w.values?.nh4 ?? null;
      const coliform = w.values?.coliform ?? null;

      let pollutedCount = 0;
      if (ph !== null && (ph < 6 || ph > 8.5)) pollutedCount++;
      if (doVal !== null && doVal < 4) pollutedCount++;
      if (bod5 !== null && bod5 > 12) pollutedCount++;
      if (cod !== null && cod > 30) pollutedCount++;
      if (nh4 !== null && nh4 > 0.5) pollutedCount++;
      if (coliform !== null && coliform > 5000) pollutedCount++;

      await pool.query(
        `INSERT INTO warnings (segment_name, ph, do_val, bod5, cod, nh4, coliform, polluted_count)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
        [segmentName, ph, doVal, bod5, cod, nh4, coliform, pollutedCount]
      );
    }

    res.json({ success: true, count: warnings.length });

  } catch (err) {
    console.error('❌ Lỗi lưu cảnh báo route cũ:', err);
    res.status(500).json({ error: 'Lỗi server', detail: err.message });
  }
});

/* =========================================================
   5) LẤY DANH SÁCH CẢNH BÁO MỚI NHẤT
========================================================= */
app.get('/api/reports/latest', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT id, segment_name, ph, do_val, bod5, cod, nh4, coliform, polluted_count, report_date
      FROM warnings
      ORDER BY report_date DESC
      LIMIT 100
    `);

    res.json(result.rows);

  } catch (err) {
    console.error('❌ Lỗi lấy warnings:', err);
    res.status(500).json({ error: 'Lỗi server' });
  }
});

/* =========================================================
   6) ĐĂNG KÝ
========================================================= */
app.post('/api/register', async (req, res) => {

  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({
      success: false,
      message: 'Thiếu thông tin'
    });
  }

  try {

    const checkUser = await pool.query(
      'SELECT * FROM users WHERE username = $1',
      [username]
    );

    if (checkUser.rows.length > 0) {
      return res.json({
        success: false,
        message: 'Tên đăng nhập đã tồn tại'
      });
    }

    await pool.query(
      'INSERT INTO users(username,password) VALUES($1,$2)',
      [username, password]
    );

    res.json({
      success: true,
      message: 'Đăng ký thành công'
    });

  } catch (err) {

    console.error('❌ Register error:', err);

    res.status(500).json({
      success: false,
      message: err.message
    });

  }

});


/* =========================================================
   7) ĐĂNG NHẬP
========================================================= */
app.post('/api/login', async (req, res) => {

  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({
      success: false,
      message: 'Thiếu thông tin'
    });
  }

  try {

    const result = await pool.query(
      'SELECT * FROM users WHERE username = $1 AND password = $2',
      [username, password]
    );

    if (result.rows.length === 0) {
      return res.json({
        success: false,
        message: 'Sai tài khoản hoặc mật khẩu'
      });
    }

    res.json({
      success: true,
      message: 'Đăng nhập thành công'
    });

  } catch (err) {

    console.error('❌ Login error:', err);

    res.status(500).json({
      success: false,
      message: err.message
    });

  }

});

/* =========================================================
   8) THỐNG KÊ BÁO CÁO
========================================================= */
app.get('/api/report-summary', async (req, res) => {

  try {

    const result = await pool.query(`
      SELECT
        COUNT(*) AS total_warnings,
        COUNT(*) FILTER (WHERE polluted_count > 0) AS polluted
      FROM warnings
    `);

    res.json(result.rows[0]);

  } catch(err){

    console.error(err);

    res.status(500).json({
      error: err.message
    });

  }

});

/* =========================================================
   9) DANH SÁCH ĐOẠN SÔNG
========================================================= */
app.get('/api/rivers', async (req, res) => {

  try {

    const result = await pool.query(`
      SELECT DISTINCT segment_name
      FROM warnings
      ORDER BY segment_name
    `);

    res.json(result.rows);

  } catch(err){

    res.status(500).json({
      error: err.message
    });

  }

});

/* =========================================================
   TỔNG SỐ CẢNH BÁO
========================================================= */
app.get('/api/warnings/count', async (req, res) => {

  try {

    const result = await pool.query(`
      SELECT COUNT(*) AS total_warnings
      FROM warnings
      WHERE polluted_count > 0
    `);

    res.json({
      totalWarnings: parseInt(result.rows[0].total_warnings)
    });

  } catch (err) {

    console.error('❌ Lỗi đếm cảnh báo:', err);

    res.status(500).json({
      error: err.message
    });

  }

});

app.post('/api/chat/new', async (req, res) => {

    try {

        const result = await pool.query(`
            INSERT INTO chat_sessions(title)
            VALUES ('Chat mới')
            RETURNING id
        `);

        res.json({
            sessionId: result.rows[0].id
        });

    } catch(err){

        res.status(500).json({
            error: err.message
        });

    }

});

app.get('/api/chat/history', async (req, res) => {

    try {

        const result = await pool.query(`
            SELECT
                id,
                title
            FROM chat_sessions
            ORDER BY created_at DESC
        `);

        res.json(result.rows);

    } catch(err){

        res.status(500).json({
            error: err.message
        });

    }

});

app.get('/api/chat/:id', async (req, res) => {

    try {

        const result = await pool.query(`
            SELECT
                role,
                content
            FROM chat_messages
            WHERE session_id = $1
            ORDER BY created_at
        `,
        [req.params.id]);

        res.json(result.rows);

    } catch(err){

        res.status(500).json({
            error: err.message
        });

    }

});
app.post('/api/chat/message', async (req,res)=>{

    const {
        sessionId,
        userMessage,
        botReply
    } = req.body;

    try{

        const session = await pool.query(
            `
            SELECT title
            FROM chat_sessions
            WHERE id = $1
            `,
            [sessionId]
        );

        if(
            session.rows.length > 0 &&
            session.rows[0].title === 'Chat mới'
        ){
            await pool.query(
                `
                UPDATE chat_sessions
                SET title = $1
                WHERE id = $2
                `,
                [
                    userMessage.substring(0,50),
                    sessionId
                ]
            );
        }

        await pool.query(
            `
            INSERT INTO chat_messages
            (session_id,role,content)
            VALUES ($1,$2,$3)
            `,
            [
                sessionId,
                'user',
                userMessage
            ]
        );

        await pool.query(
            `
            INSERT INTO chat_messages
            (session_id,role,content)
            VALUES ($1,$2,$3)
            `,
            [
                sessionId,
                'assistant',
                botReply
            ]
        );

        res.json({
            success:true
        });

    }catch(err){

        console.error(err);

        res.status(500).json({
            error:err.message
        });

    }

});

app.listen(port, () => {
  console.log(`✅ Server running at http://localhost:${port}`);
});