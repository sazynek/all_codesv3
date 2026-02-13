import asyncio
import os
import random
import pandas as pd  # type:ignore
from datetime import datetime
from TikTokApi import TikTokApi  # type:ignore
from array_users import usernames

# Настройки
ms_token = os.environ.get(
    "cE9L225OHWP5x_g-W8DyLVC2fP-S98KZK6cHsJA6uEtUyuDKfa6ZkT-G4VON8jNvlbyhLYt6oEvRXb8wpExttMipxDIv57g0SjDriyjJxBmwB57sRxZhSCbMO-5i_OvUwPpTUVbQ2pE=",
    None,
)
EXCEL_BACKUP = "tiktok_backup.xlsx"
FINAL_QUALIFIED = "tiktok_qualified.xlsx"


def final_qualified():
    if os.path.exists(EXCEL_BACKUP):
        df = pd.read_excel(EXCEL_BACKUP)  # type:ignore
        cols = [
            "user",
            "days_since_last_post",
            "posts_last_30_days",
            "max_views_last_20",
            "median_views_last_20",
        ]
        df[df["passed"] == True][cols].to_excel(
            FINAL_QUALIFIED, index=False
        )  # type:ignore
        print(f"\n[*] Скан окончен. Подходящие аккаунты в: {FINAL_QUALIFIED}")


def save_to_backup(new_results):  # type:ignore
    """Интеллектуальное сохранение в Excel без дублей"""
    if not new_results:
        return
    new_df = pd.DataFrame(new_results)  # type:ignore
    if os.path.exists(EXCEL_BACKUP):
        try:
            old_df = pd.read_excel(EXCEL_BACKUP)  # type:ignore
            final_df = pd.concat([old_df, new_df]).drop_duplicates(
                subset=["user"], keep="last"
            )
        except Exception:
            final_df = new_df
    else:
        final_df = new_df
    final_df.to_excel(EXCEL_BACKUP, index=False)  # type:ignore
    print(f"--- [DISK] Бэкап обновлен. Записей в базе: {len(final_df)} ---")


async def process_all_users():
    results_list = []
    checked_users = set()  # type:ignore

    # Загружаем уже проверенных
    if os.path.exists(EXCEL_BACKUP):
        try:
            temp_df = pd.read_excel(EXCEL_BACKUP)  # type:ignore
            checked_users = set(temp_df["user"].astype(str).tolist())
            print(f"[*] Пропускаем уже проверенных: {len(checked_users)}")
        except:
            pass

    async with TikTokApi() as api:
        print("[*] Инициализация webkit...")
        await api.create_sessions(
            ms_tokens=[ms_token],  # type:ignore
            num_sessions=1,
            sleep_after=random.randint(5, 8),
            browser="chromium",
            headless=False,
            # proxies=[],
        )

        try:
            for idx, username in enumerate(usernames):
                if username in checked_users:
                    continue

                attempts = 0
                max_attempts = 2

                while attempts < max_attempts:
                    attempts += 1
                    prefix = (
                        f"[{idx+1}/{len(usernames)}]"
                        if attempts == 1
                        else "    [RETRY]"
                    )
                    print(f"{prefix} Анализ @{username}...")

                    try:
                        user = api.user(username=username)
                        videos_30d = []
                        now_ts = datetime.now().timestamp()

                        async for video in user.videos(count=40):  # type:ignore
                            # print(video)
                            await asyncio.sleep(random.uniform(0.5, 1.5))
                            v_data = video.as_dict
                            print("v_data=> ", v_data)
                            v_time = v_data.get("createTime", 0)
                            if now_ts - v_time > (30 * 24 * 3600):
                                break
                            videos_30d.append(v_data)

                        # РЕАЛЬНЫЕ ДАННЫЕ (0 если пусто)
                        res = {
                            "user": username,
                            "days_since_last_post": 0,
                            "posts_last_30_days": 0,
                            "max_views_last_20": 0,
                            "median_views_last_20": 0,
                            "passed": False,
                        }

                        print("Videos=> ", videos_30d)
                        if videos_30d:
                            # Получаем реальное время последнего поста из первого видео в списке
                            last_post_ts = videos_30d[0].get("createTime") or 0
                            print("TIME=> ", last_post_ts)
                            if last_post_ts > 0:
                                days_since_last = (now_ts - last_post_ts) / 86400
                            else:
                                days_since_last = 0

                            # Срез за последние 20 дней
                            v_20d = [
                                int(v.get("stats", {}).get("playCount") or 0)
                                for v in videos_30d
                                if (now_ts - (v.get("createTime") or 0))
                                <= (20 * 24 * 3600)
                            ]

                            max_v = max(v_20d) if v_20d else 0
                            avg_val = sum(v_20d) / len(v_20d) if v_20d else 0
                            count_30 = len(videos_30d)

                            # Проверка фильтров
                            cond1 = days_since_last <= 7 and last_post_ts > 0
                            cond2 = count_30 >= 10
                            cond3 = max_v >= 20000
                            cond4 = avg_val >= 1500

                            res.update(
                                {
                                    "days_since_last_post": round(
                                        max(0, days_since_last), 1
                                    ),
                                    "posts_last_30_days": count_30,
                                    "max_views_last_20": max_v,
                                    "median_views_last_20": round(avg_val, 1),
                                    "passed": all([cond1, cond2, cond3, cond4]),
                                }
                            )

                        results_list.append(res)
                        status = "✅" if res["passed"] else "❌"
                        print(
                            f"    {status} Max: {res['max_views_last_20']} | Avg(MedCol): {res['median_views_last_20']}"
                        )
                        break

                    except Exception as e:
                        err_msg = str(e).lower()
                        if (
                            "empty response" in err_msg
                            or "detecting you're a bot" in err_msg
                        ) and attempts < max_attempts:
                            wait_bot = random.randint(70, 80)
                            print(
                                f"    [!] ДЕТЕКТ БОТА: Спим {wait_bot} сек. Пройдите капчу в окне!"
                            )
                            await asyncio.sleep(wait_bot)
                            continue
                        else:
                            print(f"    (!) Ошибка на @{username}: {e}. Пропускаем.")
                            break

                # Бэкап каждые 5 пользователей
                if (idx + 1) % 5 == 0:
                    save_to_backup(results_list)
                    results_list.clear()

                await asyncio.sleep(random.uniform(45, 60))

        finally:
            if results_list:
                save_to_backup(results_list)
                results_list.clear()

    final_qualified()


if __name__ == "__main__":
    try:
        asyncio.run(process_all_users())
    except KeyboardInterrupt:
        print("\n[!] Процесс остановлен пользователем.")
