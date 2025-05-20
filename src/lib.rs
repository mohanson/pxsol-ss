use solana_program::sysvar::Sysvar;

solana_program::entrypoint!(process_instruction);

pub fn process_instruction(
    program_id: &solana_program::pubkey::Pubkey,
    accounts: &[solana_program::account_info::AccountInfo],
    data: &[u8],
) -> solana_program::entrypoint::ProgramResult {
    let accounts_iter = &mut accounts.iter();
    let account_user = solana_program::account_info::next_account_info(accounts_iter)?;
    let account_data = solana_program::account_info::next_account_info(accounts_iter)?;
    let _ = solana_program::account_info::next_account_info(accounts_iter)?;
    let _ = solana_program::account_info::next_account_info(accounts_iter)?;

    let rent_exemption = solana_program::rent::Rent::get()?.minimum_balance(data.len());
    let bump_seed = solana_program::pubkey::Pubkey::find_program_address(
        &[&account_user.key.to_bytes()],
        program_id,
    )
    .1;
    solana_program::program::invoke_signed(
        &solana_program::system_instruction::create_account(
            account_user.key,
            account_data.key,
            rent_exemption,
            data.len() as u64,
            program_id,
        ),
        accounts,
        &[&[&account_user.key.to_bytes(), &[bump_seed]]],
    )?;
    account_data.data.borrow_mut().copy_from_slice(data);
    Ok(())
}
