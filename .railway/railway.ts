import { defineRailway, project, service } from "railway/iac";

export default defineRailway(() => {
  const web = service("Family-Tree", {
    start: "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT",
    healthcheck: "/api/relationship-types/",
    // builder from CaC: "NIXPACKS"
  });

  return project("Family-Tree", {
    resources: [web],
  });
});
