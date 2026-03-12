import { test, expect } from './fixtures'
import { login, register, logout, waitForLoading } from './helpers'

test.describe('Authentication Flow', () => {
  test('should display login page', async ({ page }) => {
    await page.goto('/login')

    // Check page title
    await expect(page).toHaveTitle(/登录|Login/)

    // Check login form elements
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible()
    await expect(page.locator('[data-testid="username-input"]')).toBeVisible()
    await expect(page.locator('[data-testid="password-input"]')).toBeVisible()
    await expect(page.locator('[data-testid="login-button"]')).toBeVisible()
  })

  test('should display register page', async ({ page }) => {
    await page.goto('/register')

    // Check page title
    await expect(page).toHaveTitle(/注册|Register/)

    // Check register form elements
    await expect(page.locator('[data-testid="register-form"]')).toBeVisible()
    await expect(page.locator('[data-testid="username-input"]')).toBeVisible()
    await expect(page.locator('[data-testid="email-input"]')).toBeVisible()
    await expect(page.locator('[data-testid="password-input"]')).toBeVisible()
    await expect(page.locator('[data-testid="confirm-password-input"]')).toBeVisible()
    await expect(page.locator('[data-testid="register-button"]')).toBeVisible()
  })

  test('should navigate between login and register pages', async ({ page }) => {
    // Start at login page
    await page.goto('/login')

    // Click register link
    await page.click('[data-testid="register-link"]')

    // Should be on register page
    await expect(page).toHaveURL(/\/register/)
    await expect(page.locator('[data-testid="register-form"]')).toBeVisible()

    // Click login link
    await page.click('[data-testid="login-link"]')

    // Should be back on login page
    await expect(page).toHaveURL(/\/login/)
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible()
  })

  test('should show validation errors for empty fields', async ({ page }) => {
    await page.goto('/login')

    // Click login without filling fields
    await page.click('[data-testid="login-button"]')

    // Should show validation errors (Element Plus form validation)
    await expect(page.locator('.el-form-item__error')).toBeVisible()
  })

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login')

    // Fill in invalid credentials
    await page.fill('[data-testid="username-input"] input', 'invaliduser')
    await page.fill('[data-testid="password-input"] input', 'wrongpassword')

    // Click login
    await page.click('[data-testid="login-button"]')

    // Should show error message
    await expect(page.locator('.el-message--error')).toBeVisible({ timeout: 10000 })
  })

  test('should login successfully with valid credentials', async ({ page, testUser }) => {
    await login(page, testUser.username, testUser.password)

    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/)

    // Should show user menu
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible()
  })

  test('should access protected pages after login', async ({ loggedInPage }) => {
    // Try accessing dashboard
    await loggedInPage.goto('/dashboard')
    await waitForLoading(loggedInPage)

    // Should be on dashboard
    await expect(loggedInPage).toHaveURL(/\/dashboard/)
    await expect(loggedInPage.locator('[data-testid="dashboard-page"]')).toBeVisible()
  })

  test('should logout successfully', async ({ page, testUser }) => {
    // Login first
    await login(page, testUser.username, testUser.password)

    // Perform logout
    await logout(page, testUser)

    // Should redirect to login page
    await expect(page).toHaveURL(/\/login/)

    // Try accessing protected page - should redirect to login
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/\/login/)
  })

  test('should persist session after page reload', async ({ page, testUser }) => {
    // Login
    await login(page, testUser.username, testUser.password)

    // Reload page
    await page.reload()
    await waitForLoading(page)

    // Should still be on dashboard (session persisted)
    await expect(page).toHaveURL(/\/dashboard/)
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible()
  })
})
