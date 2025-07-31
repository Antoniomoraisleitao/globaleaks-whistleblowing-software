describe("admin backup settings", () => {
  it("should enable backup and set time, period and destination", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.get('[data-cy="backup"]').click().should("be.visible");
    cy.get('#backup-enable').check().should('be.checked');
    cy.get('#backup-time').should('not.be.disabled').clear().type('03:30');
    cy.get('#backup-period').should('not.be.disabled').clear().type('6');
    cy.get('#backup-destination').should('not.be.disabled').clear().type('backup');
    cy.get('#save_settings').click();

    cy.visit("/#/admin/settings");
    cy.get('[data-cy="backup"]').click().should("be.visible");
    cy.get('#backup-enable').should('be.checked');
    cy.get('#backup-time').should('have.value', '03:30');
    cy.get('#backup-period').should('have.value', '6');
    cy.get('#backup-destination').should('have.value', 'backup');
    cy.logout();
  });

  it("should change backup job status (stop and restart)", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.get('[data-cy="backup"]').click().should("be.visible");
    cy.get('#backup-status').should('have.value', 'pending');
    cy.get('[data-cy="restart-job"]').click();
    cy.get('#backup-status').should('have.value', 'running');
    cy.get('[data-cy="stop-job"]').click();
    cy.get('#backup-status').should('not.have.value', 'running');
    cy.get('#backup-status').should('have.value', 'stopped');
    cy.logout();
  });

  it("should disable backup and disable fields", () => {
    cy.login_admin();
    cy.visit("/#/admin/settings");
    cy.get('[data-cy="backup"]').click().should("be.visible");
    cy.get('#backup-enable').uncheck().should('not.be.checked');
    cy.get('#backup-time').should('be.disabled');
    cy.get('#backup-period').should('be.disabled');
    cy.get('#backup-destination').should('be.disabled');
    cy.get('#save_settings').click();

    cy.visit("/#/admin/settings");
    cy.get('[data-cy="backup"]').click().should("be.visible");
    cy.get('#backup-enable').should('not.be.checked');
    cy.get('#backup-time').should('be.disabled');
    cy.get('#backup-period').should('be.disabled');
    cy.get('#backup-destination').should('be.disabled');
    cy.logout();
  });
});
