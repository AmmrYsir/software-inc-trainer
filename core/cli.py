"""
Software Inc. Trainer - Command Line Interface (CLI)
Preserved for terminal automation, batch scripting, and headless testing.
"""

import sys
import time
from .memory import get_game_memory

def run_cli(args):
    game = get_game_memory()
    print("==========================================================")
    print("           SOFTWARE INC. MEMORY TRAINER (CLI)             ")
    print("==========================================================")

    if any(a in ("--help", "-h", "/?", "help") for a in args):
        print("Usage: python trainer.py [options]")
        print("\nOptions:")
        print("  --status                  Print current game, treasury, and personnel stats")
        print("  --list-teams              List all personnel grouped by team with stats & traits")
        print("  --add-money <amount>      Add funds to corporate treasury")
        print("  --set-money <amount>      Set exact corporate treasury balance")
        print("  --add-fans <count>        Add company fans")
        print("  --set-rep <0-100>         Set business reputation percentage")
        print("  --max-founder             Max out Founder vitals, skills, specs & clear weaknesses")
        print("  --max-employees           Max out all employees' needs and base skills to 100%")
        print("  --max-specs               Elevate all employee specializations to 3 stars")
        print("  --add-spec-exp <points>   Grant specialization points across all roles")
        print("  --set-spec-points <pts>   Set exact specialization points across all roles")
        print("  --reset-spec-used         Reset spent specialization points (refund capacity)")
        print("  --remove-weaknesses       Cure/remove all 8 negative traits from all personnel")
        print("  --free-salaries           Set all personnel salaries to $0 (free labor)")
        print("  --unlock-furniture        Unlock all locked furniture and equipment")
        print("  --force-lights            Force all lights on")
        print("  --speed <multiplier>      Set game simulation speed (e.g. 1.0, 5.0)")
        print("  --list-projects           List active design, alpha, and beta projects with progress")
        print("  --list-products           List released software products and metrics")
        print("  --max-design [name]       Max design phase (100% progress, Iteration 3) for project(s)")
        print("  --max-dev [name]          Complete code & art (100%) for active alpha/beta project(s)")
        print("  --clear-bugs [name]       Clear all bugs (0) on active alpha/beta project(s)")
        print("  --promote-beta [name]     Promote project(s) to Beta phase")
        print("  --ready-release [name]    Ready project(s) for release (max dev + 0 bugs + finished)")
        print("  --set-proj-fans <name> <n> Set followers for specific project")
        print("  --add-proj-fans <n>       Add followers to all active projects")
        print("  --max-product [name]      Max quality (1.5), 100% awareness & clear bugs on product(s)")
        print("  --list-research           List active research tasks, progress (pts & %), and speed factor")
        print("  --list-patents            List corporate patents, royalty percentages, and collected income")
        print("  --max-research [spec]     Instantly complete active research task(s) and trigger patent grant")
        print("  --set-research-speed <n>  Set research speed multiplier (e.g. 5.0, 10.0, 50.0) across tasks")
        print("  --set-research-prog <s <n> Set exact progress points on active research")
        print("  --boost-patents           Boost all patents to 50% royalty and extend expiration to 2099")
        return 0

    if not game.attach():
        print("[!] ERROR: Could not attach to Software Inc.exe.")
        print("    Please ensure the game is running and a save is loaded.")
        return 1

    print(f"[+] Attached to PID:       {game.pid}")
    print(f"[+] Active Company:        {game.get_company_name()}")
    print(f"[+] Bank Balance:          ${game.get_money():,.2f}")
    print(f"[+] Fans:                  {game.get_fans():,}")
    print(f"[+] Business Reputation:   {game.get_business_rep()*100:.1f}%")

    founder = game.get_founder()
    if founder:
        print(f"[+] Founder:               {founder['name']} (Team: {founder['team']})")

    i = 0
    while i < len(args):
        cmd = args[i].lower()
        if cmd == "--add-money" and i + 1 < len(args):
            amt = float(args[i+1])
            game.add_money(amt)
            print(f"[SUCCESS] Added ${amt:,.2f}! New Balance: ${game.get_money():,.2f}")
            i += 2
        elif cmd == "--set-money" and i + 1 < len(args):
            amt = float(args[i+1])
            game.set_money(amt)
            print(f"[SUCCESS] Set Balance to ${amt:,.2f}!")
            i += 2
        elif cmd == "--add-fans" and i + 1 < len(args):
            fans = int(args[i+1])
            game.add_fans(fans)
            print(f"[SUCCESS] Added {fans:,} fans! Total Fans: {game.get_fans():,}")
            i += 2
        elif cmd == "--set-rep" and i + 1 < len(args):
            rep = float(args[i+1]) / 100.0 if float(args[i+1]) > 1.0 else float(args[i+1])
            game.set_business_rep(rep)
            print(f"[SUCCESS] Business Reputation set to {game.get_business_rep()*100:.1f}%")
            i += 2
        elif cmd == "--unlock-furniture":
            game.unlock_furniture(True)
            print("[SUCCESS] All furniture unlocked!")
            i += 1
        elif cmd == "--force-lights":
            game.force_lights(True)
            print("[SUCCESS] All lights forced ON!")
            i += 1
        elif cmd == "--max-founder":
            if founder:
                p = founder["emp_ptr"]
                game.max_employee_needs(p)
                game.max_employee_skills(p)
                sp = game.max_employee_specs(p, 3)
                game.add_employee_spec_exp(p, 50.0)
                game.remove_employee_weaknesses(p)
                print(f"[SUCCESS] Maxed Founder '{founder['name']}': 100% Needs, 100% Skills, {sp} Specs Maxed, Weaknesses Removed, +50 EXP!")
            i += 1
        elif cmd == "--max-employees":
            n = game.max_all_employees_needs()
            s = game.max_all_employees_skills()
            print(f"[SUCCESS] Maxed Needs and Skills for {n} employees & facility staff!")
            i += 1
        elif cmd == "--max-specs":
            count = game.max_all_employees_specs(3)
            print(f"[SUCCESS] Elevated {count} specializations across all employees to Level 3!")
            i += 1
        elif cmd == "--add-spec-exp" and i + 1 < len(args):
            delta = float(args[i+1])
            n = game.add_all_employees_spec_exp(delta)
            print(f"[SUCCESS] Added +{delta:.1f} Specialization Points across all roles for {n} employees!")
            i += 2
        elif cmd == "--set-spec-points" and i + 1 < len(args):
            pts = float(args[i+1])
            emps = game.get_employees()
            count = sum(1 for e in emps if game.set_all_employee_spec_points(e["emp_ptr"], pts))
            print(f"[SUCCESS] Set specialization points to {pts:.1f} across all roles for {count} employees!")
            i += 2
        elif cmd == "--reset-spec-used":
            emps = game.get_employees()
            count = sum(1 for e in emps if game.reset_employee_spec_used(e["emp_ptr"]))
            print(f"[SUCCESS] Reset spent specialization points (refunded capacity) for {count} employees!")
            i += 1
        elif cmd == "--remove-weaknesses":
            rem = game.remove_all_personnel_weaknesses()
            print(f"[SUCCESS] Removed {rem} weaknesses across all company personnel!")
            i += 1
        elif cmd == "--free-salaries":
            count = game.set_all_employees_free_salary()
            print(f"[SUCCESS] Assigned $0 salary (Free Labor) to all {count} personnel!")
            i += 1
        elif cmd == "--list-teams":
            emps = game.get_employees()
            by_team = {}
            for e in emps:
                by_team.setdefault(e["team"], []).append(e)
            print(f"\n--- Total Personnel: {len(emps)} across {len(by_team)} Teams ---")
            for tname, members in by_team.items():
                print(f"\n[Team: {tname}] ({len(members)} members)")
                for m in members:
                    tag = " [FOUNDER]" if m["founder"] else ""
                    w_tag = f" | Weaknesses: {', '.join(m['weaknesses'])}" if m['weaknesses'] else ""
                    print(f"  - {m['name']}{tag}: Salary ${m['salary']:,.0f} | Energy {m['energy']*100:.0f}% | Stress {m['stress']*100:.0f}% | Points: {m['total_points']}{w_tag}")
            i += 1
        elif cmd == "--speed" and i + 1 < len(args):
            spd = float(args[i+1])
            game.set_game_speed(spd)
            print(f"[SUCCESS] Game speed set to {spd}x")
            i += 2
        elif cmd == "--status":
            emps = game.get_employees()
            projs = game.get_active_projects()
            prods = game.get_released_products()
            print(f"[+] Total Detected Personnel: {len(emps)} (Employees + Facility Staff)")
            print(f"[+] Active Projects:         {len(projs)} in development")
            print(f"[+] Released Products:       {len(prods)} products on market")
            res_tasks = game.get_active_research()
            patents = game.get_patents()
            print(f"[+] Active Research:         {len(res_tasks)} research projects")
            print(f"[+] Patents Held:            {len(patents)} technology patents")
            i += 1
        elif cmd == "--list-projects":
            projs = game.get_active_projects()
            print(f"\n--- Active Software Projects: {len(projs)} ---")
            for p in projs:
                if p["type"] == "Design":
                    fin = " [FINISHED]" if p["has_finished"] else ""
                    print(f"  [Design] {p['name']}{fin}: Iteration {p['iteration']}/3 | Prog: {p['progress']*100:.1f}% | Followers: {p['followers']:,.0f}")
                else:
                    stage = "Beta" if p["in_beta"] else "Alpha"
                    print(f"  [{stage}] {p['name']}: Code {p['code_pct']:.1f}% | Art {p['art_pct']:.1f}% | Bugs: {p['bugs']:.1f} | Followers: {p['followers']:,.0f}")
            i += 1
        elif cmd == "--list-products":
            prods = game.get_released_products()
            print(f"\n--- Released Software Catalog: {len(prods)} ---")
            for p in prods:
                print(f"  - {p['name']}: Quality {p['quality']:.2f} | Fans: {p['followers']:,} | Awareness: {p['awareness']*100:.1f}% | Bugs: {p['bugs']} | Users: {p['userbase']:,} | Price: ${p['price']:.2f}")
            i += 1
        elif cmd == "--max-design":
            target_name = args[i+1].lower() if i + 1 < len(args) and not args[i+1].startswith("--") else ""
            if target_name:
                i += 2
            else:
                i += 1
            projs = game.get_active_projects()
            cnt = 0
            for p in projs:
                if p["type"] == "Design" and (not target_name or target_name in p["name"].lower() or target_name == "all"):
                    game.max_design_project(p["ptr"])
                    print(f"[SUCCESS] Maxed design for '{p['name']}' (Iteration 3, 100% Progress, Ready for Dev)!")
                    cnt += 1
            if cnt == 0:
                print("[!] No matching active design project found.")
        elif cmd == "--max-dev":
            target_name = args[i+1].lower() if i + 1 < len(args) and not args[i+1].startswith("--") else ""
            if target_name:
                i += 2
            else:
                i += 1
            projs = game.get_active_projects()
            cnt = 0
            for p in projs:
                if p["type"] in ("Alpha", "Beta") and (not target_name or target_name in p["name"].lower() or target_name == "all"):
                    game.max_dev_project(p["ptr"])
                    print(f"[SUCCESS] Completed 100% code & art programming for '{p['name']}'!")
                    cnt += 1
            if cnt == 0:
                print("[!] No matching active dev project found.")
        elif cmd == "--clear-bugs":
            target_name = args[i+1].lower() if i + 1 < len(args) and not args[i+1].startswith("--") else ""
            if target_name:
                i += 2
            else:
                i += 1
            projs = game.get_active_projects()
            cnt = 0
            for p in projs:
                if p["type"] in ("Alpha", "Beta") and (not target_name or target_name in p["name"].lower() or target_name == "all"):
                    game.clear_project_bugs(p["ptr"])
                    print(f"[SUCCESS] Cleared all bugs (0) for '{p['name']}'!")
                    cnt += 1
            if cnt == 0:
                print("[!] No matching active project found.")
        elif cmd == "--promote-beta":
            target_name = args[i+1].lower() if i + 1 < len(args) and not args[i+1].startswith("--") else ""
            if target_name:
                i += 2
            else:
                i += 1
            projs = game.get_active_projects()
            cnt = 0
            for p in projs:
                if p["type"] == "Alpha" and (not target_name or target_name in p["name"].lower() or target_name == "all"):
                    game.promote_project_to_beta(p["ptr"])
                    print(f"[SUCCESS] Promoted '{p['name']}' to Beta phase!")
                    cnt += 1
            if cnt == 0:
                print("[!] No matching active alpha project found.")
        elif cmd == "--ready-release":
            target_name = args[i+1].lower() if i + 1 < len(args) and not args[i+1].startswith("--") else ""
            if target_name:
                i += 2
            else:
                i += 1
            projs = game.get_active_projects()
            cnt = 0
            for p in projs:
                if p["type"] in ("Alpha", "Beta") and (not target_name or target_name in p["name"].lower() or target_name == "all"):
                    game.ready_project_for_release(p["ptr"])
                    print(f"[SUCCESS] Prepared '{p['name']}' for release (Code/Art maxed, 0 bugs, ready)!")
                    cnt += 1
            if cnt == 0:
                print("[!] No matching active project found.")
        elif cmd == "--set-proj-fans" and i + 2 < len(args):
            proj_name = args[i+1].lower()
            val = float(args[i+2])
            projs = game.get_active_projects()
            cnt = 0
            for p in projs:
                if proj_name in p["name"].lower() or proj_name == "all":
                    game.set_project_followers(p["ptr"], val)
                    print(f"[SUCCESS] Set followers to {val:,.0f} on '{p['name']}'!")
                    cnt += 1
            if cnt == 0:
                print(f"[!] No active project matching '{proj_name}' found.")
            i += 3
        elif cmd == "--add-proj-fans" and i + 1 < len(args):
            val = float(args[i+1])
            cnt = game.add_all_projects_followers(val)
            print(f"[SUCCESS] Added +{val:,.0f} followers across {cnt} active projects!")
            i += 2
        elif cmd == "--max-product":
            prod_name = args[i+1].lower() if i + 1 < len(args) and not args[i+1].startswith("--") else ""
            if prod_name:
                i += 2
            else:
                i += 1
            prods = game.get_released_products()
            cnt = 0
            for p in prods:
                if not prod_name or prod_name in p["name"].lower() or prod_name == "all":
                    game.modify_released_product(p["ptr"], quality=1.5, awareness=1.0, clear_bugs=True)
                    print(f"[SUCCESS] Maxed quality (1.5), 100% awareness, and cleared bugs for '{p['name']}'!")
                    cnt += 1
            if cnt == 0:
                print("[!] No matching released product found.")
        elif cmd == "--list-research":
            tasks = game.get_active_research()
            print(f"\n--- Active Research Tasks: {len(tasks)} ---")
            if not tasks:
                print("  (No active research tasks in progress)")
            for t in tasks:
                fin = " [FINISHED]" if t["finished"] else ""
                paused = " [PAUSED]" if t["paused"] else ""
                print(f"  - [{t['spec']} - {t['year_display']}]{fin}{paused}: {t['progress']:.2f} / {t['max']} pts ({t['pct']:.1f}%) | Speed: {t['upg_factor']:.1f}x")
            i += 1
        elif cmd == "--list-patents":
            patents = game.get_patents()
            print(f"\n--- Corporate Patents Catalog: {len(patents)} ---")
            if not patents:
                print("  (No patents held yet)")
            for p in patents:
                print(f"  - [{p['spec']} - {p['year_display']}]: Royalty: {p['royalty']*100:.1f}% | Revenue: ${p['income']:,.2f} | Expires: Year {p['outdates']}")
            i += 1
        elif cmd == "--max-research":
            target_spec = args[i+1].lower() if i + 1 < len(args) and not args[i+1].startswith("--") else ""
            if target_spec:
                i += 2
            else:
                i += 1
            tasks = game.get_active_research()
            cnt = 0
            for t in tasks:
                if not target_spec or target_spec in t["spec"].lower() or target_spec == "all":
                    game.max_research_task(t["ptr"])
                    print(f"[SUCCESS] Completed research on '{t['spec']} - {t['year_display']}' (Max points awarded, Finished flag set)!")
                    cnt += 1
            if cnt == 0:
                print("[!] No matching active research task found.")
        elif cmd == "--set-research-speed" and i + 1 < len(args):
            factor = float(args[i+1])
            cnt = game.boost_all_active_research(factor)
            print(f"[SUCCESS] Set research speed multiplier to {factor:.1f}x across {cnt} active research tasks!")
            i += 2
        elif cmd == "--set-research-prog" and i + 2 < len(args):
            target_spec = args[i+1].lower()
            pts = float(args[i+2])
            tasks = game.get_active_research()
            cnt = 0
            for t in tasks:
                if target_spec in t["spec"].lower() or target_spec == "all":
                    game.set_research_progress(t["ptr"], pts)
                    print(f"[SUCCESS] Set research progress to {pts:.2f} pts on '{t['spec']} - {t['year_display']}'!")
                    cnt += 1
            if cnt == 0:
                print(f"[!] No active research task matching '{target_spec}' found.")
            i += 3
        elif cmd == "--boost-patents":
            cnt = game.boost_all_patents(royalty=0.50, outdates=2099)
            print(f"[SUCCESS] Boosted {cnt} patents: Set royalties to 50% and extended expiration to Year 2099!")
            i += 1
        else:
            i += 1

    return 0

