import { describe, expect, it } from "vitest";
import GroupCard from "../components/GroupCard";
import { render, screen } from "./test-utils";

describe("GroupCard", () => {
	const mockGroup = {
		letter: "A",
		teams: [
			{
				id: 1,
				name: "Germany",
				flag: "🇩🇪",
				played: 3,
				won: 2,
				draw: 1,
				lost: 0,
				goalsFor: 6,
				goalsAgainst: 2,
				points: 7,
				rank: 1,
			},
			{
				id: 2,
				name: "Scotland",
				flag: "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
				played: 3,
				won: 1,
				draw: 1,
				lost: 1,
				goalsFor: 2,
				goalsAgainst: 4,
				points: 4,
				rank: 2,
			},
			{
				id: 3,
				name: "Hungary",
				flag: "🇭🇺",
				played: 3,
				won: 1,
				draw: 0,
				lost: 2,
				goalsFor: 2,
				goalsAgainst: 5,
				points: 3,
				rank: 3,
			},
			{
				id: 4,
				name: "Switzerland",
				flag: "🇨🇭",
				played: 3,
				won: 0,
				draw: 2,
				lost: 1,
				goalsFor: 2,
				goalsAgainst: 3,
				points: 2,
				rank: 4,
			},
		],
	};

	it("renders group letter and team names", () => {
		render(<GroupCard group={mockGroup} />);

		// Norwegian translation: "Gruppe A"
		expect(screen.getByText(/Gruppe/)).toBeDefined();
		expect(screen.getByText(/A/)).toBeDefined();
		expect(screen.getByText("Germany")).toBeDefined();
		expect(screen.getByText("Scotland")).toBeDefined();
	});

	it("displays team flag emojis", () => {
		render(<GroupCard group={mockGroup} />);
		expect(screen.getByText("🇩🇪")).toBeDefined();
	});

	it("displays correct points and goal difference", () => {
		render(<GroupCard group={mockGroup} />);
		// Germany: 7 points, +4 GD
		// Use getAllByText since multiple cells may have the same value
		expect(screen.getAllByText("7").length).toBeGreaterThan(0);
		expect(screen.getAllByText("4").length).toBeGreaterThan(0);
	});

	it("highlights top 2 teams as qualifiers", () => {
		const { container } = render(<GroupCard group={mockGroup} />);
		// This depends on how highlighting is implemented (e.g., CSS class)
		// Component uses bg-emerald for qualifiers
		const rows = container.querySelectorAll("tr");
		// row 0 is header, row 1 is Germany, row 2 is Scotland
		expect(rows[1].className).toContain("bg-emerald");
		expect(rows[2].className).toContain("bg-emerald");
	});

	it("styles 3rd place team differently", () => {
		const { container } = render(<GroupCard group={mockGroup} />);
		const rows = container.querySelectorAll("tr");
		// row 3 is Hungary (3rd place)
		expect(rows[3].className).toContain("bg-yellow");
	});
});
