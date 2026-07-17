"""
Module: persistence.discover_repo

Purpose:
    Repository for Discover-tab personalization queries: bandit-ranked
    "Untuk Kamu" artists, "Belum Pernah Kamu Dengar" (unheard) artists,
    genre taste spectrum, genre affinity, and artist detail lookup.

    Split out from `artist_repo.py` / `genre_repo.py` on purpose (see
    docs/PATCHLOG.md PATCH-2026-07-17-070): those two repos own click/reward
    *tracking*, this one owns Discover *personalization reads* built on top
    of that data. Same split as `LibraryRepository` vs `TrackRepository`.

Responsibilities:
    - get_bandit_ranked_artists / get_unheard_artists — "Untuk Kamu" /
      "Belum Pernah Kamu Dengar" sections.
    - get_taste_spectrum / get_top_genre — genre listening-history breakdown.
    - get_genre_artists_enriched — artists for a given genre, with cover+tags.
    - get_artist_detail — full detail (genres + up to 10 songs) for a sheet.

Depends on:
    - persistence.discover_enrich

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import structlog

from persistence.discover_enrich import enrich_artists

logger = structlog.get_logger(__name__)


class DiscoverRepository:
    def __init__(self, conn):
        self._conn = conn

    async def get_bandit_ranked_artists(self, limit: int = 10) -> list[dict]:
        """ "Untuk Kamu": artis yang bandit (reward_alpha/beta) sudah pernah
        belajar sesuatu tentangnya (bukan default alpha=beta=1), diurut
        berdasarkan posterior mean alpha/(alpha+beta) — makin tinggi makin
        besar kemungkinan disukai user. Tiap hasil dapat field `match_pct`
        (0-100, dibulatkan) untuk ditampilkan di kartu.
        """
        if not self._conn:
            return []
        query = """
            SELECT id, nama, kategori, tahun_aktif,
                   COALESCE(reward_alpha, 1) AS reward_alpha,
                   COALESCE(reward_beta, 1) AS reward_beta
            FROM artists
            WHERE COALESCE(reward_alpha, 1) > 1 OR COALESCE(reward_beta, 1) > 1
            ORDER BY (CAST(COALESCE(reward_alpha, 1) AS REAL)
                      / (COALESCE(reward_alpha, 1) + COALESCE(reward_beta, 1))) DESC
            LIMIT ?
        """
        try:
            async with self._conn.execute(query, (limit,)) as cursor:
                rows = [dict(r) for r in await cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting bandit ranked artists: {e}")
            return []

        for row in rows:
            alpha, beta = row["reward_alpha"], row["reward_beta"]
            row["match_pct"] = round(100 * alpha / (alpha + beta))

        return await enrich_artists(self._conn, rows)

    async def get_unheard_artists(self, limit: int = 10) -> list[dict]:
        """ "Belum Pernah Kamu Dengar": artis yang bandit belum pernah
        disentuh sama sekali (alpha=beta=1, artinya belum ada
        completion/skip tercatat) DAN belum pernah di-klik dari Discover
        (click_count=0) — supaya section ini benar-benar berisi hal baru,
        bukan sesuatu yang user sudah pernah lihat tapi belum diputar.
        """
        if not self._conn:
            return []
        query = """
            SELECT id, nama, kategori, tahun_aktif
            FROM artists
            WHERE COALESCE(reward_alpha, 1) = 1
              AND COALESCE(reward_beta, 1) = 1
              AND COALESCE(click_count, 0) = 0
            ORDER BY RANDOM()
            LIMIT ?
        """
        try:
            async with self._conn.execute(query, (limit,)) as cursor:
                rows = [dict(r) for r in await cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting unheard artists: {e}")
            return []

        return await enrich_artists(self._conn, rows)

    async def get_taste_spectrum(self, limit: int = 6) -> list[dict]:
        """Agregasi genre dari histori putar: SUM(play_count +
        is_favorite*3) per genre, dinormalisasi ke persentase. Genre di
        luar top-(limit-1) digabung ke satu bucket "Lainnya" supaya bar
        tidak pecah jadi puluhan slice tipis.

        Caveat (lihat AI_CONTEXT / implementation-plan): join
        tracks.artist -> artists.nama hanya reliable untuk lagu yang
        datang dari Radio Mode/library; lagu hasil pencarian bebas
        (nama artist beda karena uploader YouTube) tidak ikut kehitung.
        Ini batasan yang diketahui, bukan bug.

        Return [] kalau histori kosong (tracks tidak ber-genre sama
        sekali) — caller (discover_service/frontend) bertanggung jawab
        menampilkan fallback UI untuk kasus ini, bukan repo ini.
        """
        if not self._conn:
            return []
        query = """
            SELECT g.nama_genre AS genre,
                   SUM(t.play_count + t.is_favorite * 3) AS score
            FROM tracks t
            JOIN artists a ON a.nama = t.artist
            JOIN artist_genres ag ON ag.artist_id = a.id
            JOIN genres g ON g.id = ag.genre_id
            GROUP BY g.nama_genre
            HAVING score > 0
            ORDER BY score DESC
        """
        try:
            async with self._conn.execute(query) as cursor:
                rows = [dict(r) for r in await cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting taste spectrum: {e}")
            return []

        if not rows:
            return []

        total = sum(r["score"] for r in rows)
        if total <= 0:
            return []

        top = rows[: max(limit - 1, 1)] if limit > 1 else rows[:1]
        rest = rows[len(top) :]

        spectrum = [{"genre": r["genre"], "pct": round(100 * r["score"] / total)} for r in top]
        if rest:
            rest_score = sum(r["score"] for r in rest)
            if rest_score > 0:
                spectrum.append({"genre": "Lainnya", "pct": round(100 * rest_score / total)})

        return spectrum

    async def get_top_genre(self) -> str | None:
        """Genre teratas dari taste spectrum, atau None kalau histori
        kosong (dipakai untuk seed section "Karena Kamu Suka [Genre]").
        """
        spectrum = await self.get_taste_spectrum(limit=1)
        if not spectrum:
            return None
        return spectrum[0]["genre"]

    async def get_genre_artists_enriched(self, genre_name: str, limit: int = 4) -> list[dict]:
        """Versi `GenreRepository.get_genre_artists` yang mengembalikan
        row lengkap (bukan cuma nama) sudah di-enrich cover+genre, untuk
        dipakai kartu artis di section "Karena Kamu Suka [Genre]".
        """
        if not self._conn:
            return []
        query = """
            SELECT a.id, a.nama, a.kategori, a.tahun_aktif
            FROM artists a
            JOIN artist_genres ag ON a.id = ag.artist_id
            JOIN genres g ON ag.genre_id = g.id
            WHERE g.nama_genre = ?
            ORDER BY RANDOM()
            LIMIT ?
        """
        try:
            async with self._conn.execute(query, (genre_name, limit)) as cursor:
                rows = [dict(r) for r in await cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting genre artists enriched: {e}")
            return []

        return await enrich_artists(self._conn, rows)

    async def get_artist_detail(self, nama: str) -> dict | None:
        """Info lengkap satu artis untuk detail sheet: data dasar + cover +
        genre tags + hingga 10 lagu. Return None kalau artis tidak
        ditemukan (caller balas error/empty state, bukan sheet kosong).
        """
        if not self._conn:
            return None
        try:
            async with self._conn.execute(
                "SELECT id, nama, kategori, tahun_aktif FROM artists WHERE nama = ?",
                (nama,),
            ) as cursor:
                artist_row = await cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting artist detail: {e}")
            return None

        if not artist_row:
            return None

        artist = dict(artist_row)
        enriched = await enrich_artists(self._conn, [artist])
        detail = enriched[0]

        try:
            async with self._conn.execute(
                """
                SELECT youtube_id, judul, duration FROM songs
                WHERE artist_id = ?
                ORDER BY id
                LIMIT 10
                """,
                (artist["id"],),
            ) as cursor:
                song_rows = await cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting artist detail songs: {e}")
            song_rows = []

        detail["songs"] = [
            {
                "video_id": row["youtube_id"],
                "title": row["judul"],
                "duration": row["duration"],
                "thumbnail": f"https://i.ytimg.com/vi/{row['youtube_id']}/mqdefault.jpg",
            }
            for row in song_rows
        ]
        return detail
