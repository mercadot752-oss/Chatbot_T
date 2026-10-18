import { expect, test } from "@playwright/test";

test("el portal abre el asistente institucional", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Tu vida académica, en un solo lugar" })
  ).toBeVisible();
  await page.getByRole("link", { name: /Hablar con PromeIA/ }).click();
  await expect(
    page.getByRole("heading", { name: "¿En qué puedo ayudarte?" })
  ).toBeVisible();
});

test("el chat reconoce un perfil con rol usuario desde la base", async ({ page }) => {
  await page.goto("/chatbot");
  await page.getByRole("textbox", { name: "Escribe tu mensaje para PromeIA" }).fill("999000001");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();

  await expect(page.getByText(/Tipo de usuario: usuario/)).toBeVisible();
});

test("el chat reconoce un perfil con rol profesor desde la base", async ({ page }) => {
  await page.goto("/chatbot");
  await page.getByRole("textbox", { name: "Escribe tu mensaje para PromeIA" }).fill("999000002");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();

  await expect(page.getByText(/Tipo de usuario: profesor/)).toBeVisible();
});

test("una identificación inexistente recibe un aviso sin usar datos personales", async ({ page }) => {
  await page.goto("/chatbot");
  await page.getByRole("textbox", { name: "Escribe tu mensaje para PromeIA" }).fill("999000099");
  await page.getByRole("button", { name: "Enviar mensaje" }).click();

  await expect(page.getByText(/No encontré la identificación/)).toBeVisible();
});
