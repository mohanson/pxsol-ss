solana_program::entrypoint!(process_instruction);

pub fn process_instruction(
    _: &solana_program::pubkey::Pubkey,
    _: &[solana_program::account_info::AccountInfo],
    _: &[u8],
) -> solana_program::entrypoint::ProgramResult {
    solana_program::msg!("Hello, Solana!");
    Ok(())
}
