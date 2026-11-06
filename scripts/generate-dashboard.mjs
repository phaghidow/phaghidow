import { mkdir, writeFile } from "node:fs/promises";

const username = "phaghidow";
const headers = { "User-Agent": "phaghidow-profile-readme", Accept: "application/vnd.github+json" };

async function github(path) {
  const response = await fetch(`https://api.github.com${path}`, { headers });
  if (!response.ok) throw new Error(`GitHub API ${response.status} for ${path}`);
  return response.json();
}

const escape = (value) => String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;" })[char]);
const text = (value, x, y, size = 14, color = "#92929D", anchor = "start") =>
  `<text x="${x}" y="${y}" fill="${color}" font-size="${size}" text-anchor="${anchor}">${escape(value)}</text>`;

let profile;
let repos;
let events;
try {
  [profile, repos, events] = await Promise.all([
    github(`/users/${username}`),
    github(`/users/${username}/repos?per_page=100&type=owner&sort=updated`),
    github(`/users/${username}/events/public?per_page=10`),
  ]);
} catch (error) {
  console.error(error);
  process.exitCode = 1;
  await writeFile("assets/dashboard.svg", `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 360"><rect width="1200" height="360" rx="8" fill="#101014"/><text x="600" y="175" fill="#F4F4F0" font-family="monospace" font-size="18" text-anchor="middle">ACTIVITY SIGNAL / TEMPORARILY OFFLINE</text><text x="600" y="210" fill="#92929D" font-family="monospace" font-size="12" text-anchor="middle">The next scheduled sync will retry the public GitHub API.</text></svg>`);
  process.exit();
}

const stars = repos.reduce((sum, repo) => sum + repo.stargazers_count, 0);
const recent = events.filter((event) => ["PushEvent", "CreateEvent", "PullRequestEvent", "IssuesEvent"].includes(event.type)).length;
const updated = new Date().toISOString().slice(0, 10);
const metric = (label, value, x) => `${text(label, x, 88, 12, "#92929D", "middle")}${text(value, x, 145, 42, "#F4F4F0", "middle")}`;
const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 360" role="img" aria-labelledby="title desc">
  <title id="title">GitHub activity signal for ${username}</title>
  <desc id="desc">Live public repository, follower, star, and recent activity metrics.</desc>
  <rect width="1200" height="360" rx="8" fill="#101014"/>
  <g fill="none" stroke="#2B2B34"><path d="M40 190h1120M40 250h1120"/><path d="M300 55v210M600 55v210M900 55v265"/></g>
  <g font-family="ui-monospace, SFMono-Regular, Menlo, monospace">
    ${text("PUBLIC SIGNAL / PHAGHIDOW", 40, 42, 13, "#F4F4F0")}
    ${text(`SYNCED ${updated}`, 1160, 42, 11, "#92929D", "end")}
    ${metric("REPOSITORIES", profile.public_repos, 150)}
    ${metric("FOLLOWERS", profile.followers, 450)}
    ${metric("STARS RECEIVED", stars, 750)}
    ${metric("RECENT EVENTS", recent, 1050)}
    ${text("Public REST API snapshot. Contribution history is linked to GitHub rather than approximated here.", 40, 310, 12, "#92929D")}
    <circle cx="40" cy="42" r="3" fill="#C8FF00"><animate attributeName="opacity" values=".25;1;.25" dur="2.4s" repeatCount="indefinite"/></circle>
  </g>
</svg>`;

await mkdir("assets", { recursive: true });
await writeFile("assets/dashboard.svg", svg);
