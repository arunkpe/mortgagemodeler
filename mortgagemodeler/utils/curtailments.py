from decimal import Decimal
import click

def parse_curtailments(curtailment_str: str) -> dict[int, Decimal]:
    """
    Parse a string of curtailments in the format 'amount@month,...'
    into a dictionary {month: amount}.

    Example:
        '100000@73,50000@85' => {73: Decimal('100000'), 85: Decimal('50000')}

    Parameters
    ----------
    curtailment_str : str
        String of comma-separated curtailments, each in the form 'amount@month'.

    Returns
    -------
    dict[int, Decimal]
        A dictionary mapping month numbers to curtailment amounts.

    Raises
    ------
    click.ClickException
        If the input format is invalid.
    """
    result = {}
    for entry in curtailment_str.split(","):
        try:
            amount, month = entry.split("@")
            result[int(month.strip())] = Decimal(amount.strip())
        except Exception:
            raise click.ClickException(
                f"Invalid curtailment format: {entry}. Use 'amount@month'")
    return result
