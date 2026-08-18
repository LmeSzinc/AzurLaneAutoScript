import { render } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";

import DynamicForm from "./DynamicForm.svelte";

const args = {
  Fleet1: { type: "select", value: 1, option: [1, 2, 3, 4, 5, 6] },
  Fleet1Step: { type: "select", value: 3, option: [2, 3, 4, 5] },
  Fleet2: { type: "select", value: 2, option: [0, 1, 2, 3, 4, 5, 6] },
  FleetOrder: {
    type: "select",
    value: "fleet1_mob_fleet2_boss",
    option: [
      "fleet1_mob_fleet2_boss",
      "fleet1_boss_fleet2_mob",
      "fleet1_all_fleet2_standby",
      "fleet1_standby_fleet2_all",
    ],
  },
};

const config = {
  Main: {
    Fleet: {
      Fleet1: 1,
      Fleet1Step: 5,
      Fleet2: 2,
      FleetOrder: "fleet1_mob_fleet2_boss",
    },
  },
};

describe("DynamicForm select values", () => {
  it("selects show the config values (not empty)", () => {
    render(DynamicForm, { props: { args, group: "Fleet", task: "Main", config, onsave: () => {} } });
    const selects = document.querySelectorAll("select");
    const values = Array.from(selects).map((s) => ({ value: s.value, text: s.options[s.selectedIndex]?.textContent }));
    console.log("selects:", JSON.stringify(values));
    expect(selects).toHaveLength(4);
    expect(selects[0].value).toBe("1"); // Fleet1
    expect(selects[1].value).toBe("5"); // Fleet1Step (config value, not default 3)
    expect(selects[2].value).toBe("2"); // Fleet2
    expect(selects[3].value).toBe("fleet1_mob_fleet2_boss");
  });
});
