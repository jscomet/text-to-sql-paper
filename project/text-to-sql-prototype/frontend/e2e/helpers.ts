import type { Page } from '@playwright/test'

/**
 * Wait for page loading to complete
 * Waits for loading overlay to disappear
 */
export async function waitForLoading(page: Page, timeout = 30000): Promise<void> {
  // Wait for loading overlay to disappear
  const loadingOverlay = page.locator('.loading-overlay, .el-loading-mask')
  try {
    await loadingOverlay.waitFor({ state: 'hidden', timeout })
  } catch {
    // Loading overlay may not exist, that's okay
  }

  // Also wait for network to be idle
  await page.waitForLoadState('networkidle', { timeout })
}

/**
 * Login helper function
 * @param page - Playwright page
 * @param username - Username
 * @param password - Password
 */
export async function login(page: Page, username: string, password: string): Promise<void> {
  // Navigate to login page
  await page.goto('/login')

  // Wait for form to be ready
  await page.waitForSelector('[data-testid="login-form"]', { state: 'visible' })

  // Fill in credentials
  await page.fill('[data-testid="username-input"] input', username)
  await page.fill('[data-testid="password-input"] input', password)

  // Click login button
  await page.click('[data-testid="login-button"]')

  // Wait for navigation to complete
  await page.waitForURL('**/dashboard', { timeout: 10000 })

  // Wait for page to fully load
  await waitForLoading(page)
}

/**
 * Register helper function
 * @param page - Playwright page
 * @param username - Username
 * @param email - Email
 * @param password - Password
 */
export async function register(
  page: Page,
  username: string,
  email: string,
  password: string
): Promise<void> {
  // Navigate to register page
  await page.goto('/register')

  // Wait for form to be ready
  await page.waitForSelector('[data-testid="register-form"]', { state: 'visible' })

  // Fill in registration details
  await page.fill('[data-testid="username-input"] input', username)
  await page.fill('[data-testid="email-input"] input', email)
  await page.fill('[data-testid="password-input"] input', password)
  await page.fill('[data-testid="confirm-password-input"] input', password)

  // Click register button
  await page.click('[data-testid="register-button"]')

  // Wait for navigation to complete (should redirect to login or dashboard)
  await page.waitForURL(/\/(login|dashboard)/, { timeout: 10000 })
}

/**
 * Logout helper function
 * @param page - Playwright page
 */
export async function logout(page: Page): Promise<void> {
  // Click user menu
  await page.click('[data-testid="user-menu"]')

  // Click logout
  await page.click('[data-testid="logout-button"]')

  // Wait for redirect to login page
  await page.waitForURL('**/login', { timeout: 10000 })
}

/**
 * Create database connection helper
 * @param page - Playwright page
 * @param connection - Connection details
 */
export async function createConnection(
  page: Page,
  connection: {
    name: string
    host: string
    port: string
    database: string
    username: string
    password: string
  }
): Promise<void> {
  // Navigate to connections page
  await page.goto('/connections')
  await waitForLoading(page)

  // Click add connection button
  await page.click('[data-testid="add-connection-button"]')

  // Fill in connection details
  await page.fill('[data-testid="connection-name-input"] input', connection.name)
  await page.fill('[data-testid="host-input"] input', connection.host)
  await page.fill('[data-testid="port-input"] input', connection.port)
  await page.fill('[data-testid="database-input"] input', connection.database)
  await page.fill('[data-testid="username-input"] input', connection.username)
  await page.fill('[data-testid="password-input"] input', connection.password)

  // Click save button
  await page.click('[data-testid="save-connection-button"]')

  // Wait for success message
  await page.waitForSelector('.el-message--success', { timeout: 10000 })
}
